#!/usr/bin/env python3

"""
Websocket to TCP bridge for MQTT
"""

import logging
from argparse import ArgumentParser
from functools import partial

import asyncio
import websockets


class MQTTPacketiser(object):
    """
    Split a stream of bytes at MQTT control packet boundaries.
    
    .. note::
    
        Though the MQTT-over-websockets protocol does not require that MQTT
        control packets be encapsulated in individual websocket messages,
        several implementations require this in practice. As a consequence,
        this implementation also implements a simple MQTT packetiser.
    
    Sample usage::
    
        >>> p = MQTTPacketiser()
        >>> while True:
        ...     byte = await socket.read(1)
        ...     if not byte:
        ...         break
        ...     for control_packet_bytes in p.iter_packets(byte):
        ...         print(control_packet_bytes)
    """
    
    def __init__(self):
        self._packets = []
        self._processor = self._byte_processor()
        self._processor.send(None)
    
    def _byte_processor(self):
        """
        Internal. A generator which accepts bytes from a stream one at a time
        and, when a complete MQTT packet has been received, places it into
        the ``_packets`` list.
        
        This generator should be sent individual bytes (as ints). The generator
        will run forever yields only ``None``.
        """
        while True:
            packet = bytearray()
            
            header = (yield)
            packet.append(header)
            
            remaining_length = 0
            for shift in range(0, 7*3, 7):
                length_byte = (yield)
                packet.append(length_byte)
                
                remaining_length |= (length_byte & 0x7F) << shift
                
                if length_byte & 0x80 == 0x00:
                    break
            
            for byte in range(remaining_length):
                packet.append((yield))
            
            self._packets.append(packet)
    
    def iter_packets(self, bytes):
        """
        Process a bytes-like object of bytes from the stream. Returns an
        iterator over MQTT control packets in bytes-like objects. This iterator
        may be empty if no new whole control packets have been received.
        """
        for b in bytearray(bytes):
            self._processor.send(b)
        while self._packets:
            yield self._packets.pop(0)


async def websocket_to_mqtt(websocket, mqtt_writer):
    """
    Forward MQTT packets from a websocket to a TCP connection to an MQTT
    server.
    
    Parameters
    ==========
    websocket : :py:class:`websockets.WebsocketCommonProtocol`
    mqtt_writer : :py:class:`asyncio.StreamWriter`
    """
    p = MQTTPacketiser()
    
    try:
        while not mqtt_writer.is_closing():
            for packet_bytes in p.iter_packets(await websocket.recv()):
                mqtt_writer.write(packet_bytes)
                await mqtt_writer.drain()
    except websockets.ConnectionClosed:
        pass
    finally:
        mqtt_writer.close()
        await mqtt_writer.wait_closed()
        await websocket.close()


async def mqtt_to_websocket(mqtt_reader, websocket):
    """
    Forward MQTT packets from a TCP connection to an MQTT server to a
    websocket.
    
    Parameters
    ==========
    mqtt_reader : :py:class:`asyncio.StreamReader`
    websocket : :py:class:`websockets.WebsocketCommonProtocol`
    """
    p = MQTTPacketiser()
    try:
        while not websocket.closed:
            bytes = await mqtt_reader.read(1)
            if not bytes:
                break
            for packet_bytes in p.iter_packets(bytes):
                await websocket.send(packet_bytes)
    finally:
        await websocket.close()


async def serve_websocket_client(mqtt_host, mqtt_port, websocket, path):
    """
    Handle a websocket connection.
    
    Parameters
    ==========
    websocket : :py:class:`websockets.WebsocketCommonProtocol
    path : (unused)
    """
    try:
        mqtt_reader, mqtt_writer = await asyncio.open_connection(
            mqtt_host,
            mqtt_port,
        )
    except Exception as e:
        logging.warn(
            "Couldn't forward connection from %s: MQTT server down (%s)",
            websocket.remote_address,
            e,
        )
        return
    
    logging.info("Client %s connected", websocket.remote_address)
    try:
        await asyncio.gather(
            websocket_to_mqtt(websocket, mqtt_writer),
            mqtt_to_websocket(mqtt_reader, websocket),
            return_exceptions=True,
        )
    finally:
        logging.info("Client %s disconnected", websocket.remote_address)
        mqtt_writer.close()
        await websocket.close()
        await mqtt_writer.wait_closed()


def main():
    parser = ArgumentParser(description="""
        A Websocket-to-TCP bridge for MQTT.
    """)
    
    parser.add_argument(
        "--mqtt-host",
        type=str, default="localhost",
        help="""
            The hostname of the MQTT server to forward connections to (default:
            %(default)s).
        """,
    )
    
    parser.add_argument(
        "--mqtt-port",
        type=int, default=1883,
        help="""
            The port number of the MQTT server to forward connections to
            (default: %(default)s).
        """,
    )
    
    parser.add_argument(
        "--websocket-host",
        type=str, default="localhost",
        help="""
            The address to listen to for websocket connections (default:
            %(default)s).
        """,
    )
    
    parser.add_argument(
        "--websocket-port",
        type=int, default=9001,
        help="""
            The port number to listen on for websocket connections (default:
            %(default)s).
        """,
    )
    
    parser.add_argument("--verbose", "-v", action="count", default=0)
    
    args = parser.parse_args()
    
    if args.verbose > 0:
        logging.basicConfig(level=logging.INFO)
    
    start_server = websockets.serve(
        partial(
            serve_websocket_client,
            args.mqtt_host,
            args.mqtt_port,
        ),
        args.websocket_host,
        args.websocket_port,
        subprotocols=["mqtt"],
    )
    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_forever()


if __name__ == "__main__":
    main()
