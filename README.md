Websocket to TCP Bridge for MQTT
================================

This repository contains a quick-and-dirty bridge implementing the MQTT
websocket protocol for MQTT brokers which do not support it (or which implement
it badly). It is a quick and dirty affair and not production ready. It does,
however, appear to work... :)

Minimal, straight-from-the-repo usage:

    $ pip3 install "websockets>=8.1"
    $ python3 mqtt_ws_bridge.py

Or, if you prefer, install as a package:

    $ pip install mqtt_ws_bridge
    $ mqtt_ws_bridge

By default a websocket server is started listening on port 9001 on the loopback
interface. The bridge expects to find the MQTT server listening on
localhost:1883. See ``--help`` for options for overriding default port numbers
and hostnames.

This server will respond to HTTP websocket connections with no regard for the
requested path. Ideally, this interface should be hidden behind a
reverse-proxy.
