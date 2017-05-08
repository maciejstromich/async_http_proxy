# async_http_proxy

Simple Asyncronous HTTP Proxy using asyncio with /status returning uptime and transfered data in bytes.

## Building

Docker container is built using python:3.5

```
docker-compose build
```

## Running 
To run the proxy run:
```
docker-compose up
```

## Stats:

Simple stats are available at http://$(docker-machine ip):8080/status


