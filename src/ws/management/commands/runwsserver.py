import asyncio
import re

from django.core.management.base import BaseCommand
from websockets.asyncio.server import ServerConnection, serve

from ws.urls import url_patterns


# TODO: использовать джанговый распознаватель путей
# TODO: вынести в отдельную библиотеку
async def handler(websocket: ServerConnection):
    print('path is', websocket.request.path)
    for url in url_patterns:
        if len(url) == 2:
            url.append(re.compile(url[0]))

        matched_object = url[2].match(websocket.request.path)
        if matched_object:
            await url[1](websocket, **(matched_object.groupdict()))
            return

    await websocket.close()


async def main(port):
    async with serve(handler, "", port, server_header='service server'):
        await asyncio.get_running_loop().create_future()  # run forever


class Command(BaseCommand):
    help = 'Run the websocket server'

    def handle(self, *args, **options):
        port = options['addrport'] or 8001
        asyncio.run(main(port))

    def add_arguments(self, parser):
        parser.add_argument(
            'addrport', nargs='?', help='Optional port number'
        )
