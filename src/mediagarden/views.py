from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status

from mediagarden.models import AnyFile
from utils import open_file_with_default_program


class NoteView(APIView):
    def put(self, request, any_file_id):
        any_file = AnyFile.objects.filter(pk=any_file_id).first()
        if not any_file:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'message': 'file not found'})

        if not any_file.note_path.exists():
            with any_file.note_path.open('w', encoding='utf-8') as note_file:
                note_file.write(f'# {any_file.filename}\n')

        return Response(status=status.HTTP_204_NO_CONTENT)


class OpenView(APIView):
    def post(self, request, any_file_id):
        any_file = AnyFile.objects.filter(pk=any_file_id).first()
        if not any_file:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'message': 'file not found'})

        data = request.data
        what = data['what']
        if what == 'dir':
            open_file_with_default_program(any_file.absdirpath)
        elif what == 'file':
            open_file_with_default_program(any_file.abspath)

        return Response(status=status.HTTP_204_NO_CONTENT)
