from setuptools import setup, find_packages

setup(
    name="mqtt_ws_bridge",
    version="0.1.0",
    packages=find_packages(),

    # Metadata for PyPi
    url="https://github.com/mossblaser/mqtt_ws_bridge",
    author="Jonathan Heathcote",
    description="Websocket to TCP Bridge for MQTT",
    license="GPLv2",
    classifiers=[
        "Development Status :: 3 - Alpha",

        "Intended Audience :: Developers",

        "License :: OSI Approved :: GNU General Public License v2 (GPLv2)",

        "Operating System :: POSIX :: Linux",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: MacOS",

        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
    ],
    keywords="mqtt websockets",
    install_requires=["websockets>=8.1"],
    entry_points={
        "console_scripts": [
            "mqtt_ws_bridge = mqtt_ws_bridge:main",
        ],
    }
)
