from pathlib import Path

from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status

from gardensunion.base.utils import get_dj_model
from mediagarden.models import DocumentFile
from utils import open_file_with_default_program


class DocumentNoteView(APIView):
    def put(self, request, type_entity_code, any_file_id):
        gui_model = get_dj_model(int(type_entity_code))
        model_class = gui_model.dj_model

        any_file = model_class.objects.filter(pk=any_file_id).first()
        if not any_file:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'message': 'file not found'})

        if not any_file.note_path.exists():
            with any_file.note_path.open('w', encoding='utf-8') as note_file:
                note_file.write(f'# {any_file.filename}\n')

        return Response(status=status.HTTP_204_NO_CONTENT)


class DocumentOpenView(APIView):
    def post(self, request, type_entity_code, any_file_id):
        gui_model = get_dj_model(int(type_entity_code))
        model_class = gui_model.dj_model

        any_file = model_class.objects.filter(pk=any_file_id).first()
        if not any_file:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'message': 'file not found'})

        data = request.data
        what = data['what']
        if what == 'dir':
            open_file_with_default_program(any_file.absdirpath)
        elif what == 'file':
            open_file_with_default_program(any_file.abspath)

        return Response(status=status.HTTP_204_NO_CONTENT)


class ActionScanView(APIView):
    def post(self, request, type_entity_code):
        gui_model = get_dj_model(int(type_entity_code))
        model_class = gui_model.dj_model

        card = request.data['card']
        what_do = request.data['what_do']
        card_status = card['status']
        inserted_path = Path(card['inserted_path'])
        inserted_anyfile = (
            model_class.objects.filter(pk=card['inserted_id']).first()
            if card['inserted_id']
            else model_class(directory=str(inserted_path.parent), filename=inserted_path.name)
        )
        existed_anyfile = model_class.objects.filter(pk=card['existed_id']).first() if card['existed_id'] else None
        if card_status == 'new' and what_do == 'delete':
            inserted_anyfile.abspath.unlink()
            inserted_anyfile.delete()
        # elif card_status == 'moved' and what_do == 'cancel':
        #     pass
        # elif card_status == 'moved' and what_do == 'accept':
        #     pass
        elif card_status == 'dublicated' and what_do == 'delete_inserted':
            inserted_anyfile.abspath.unlink()
        elif card_status == 'dublicated' and what_do == 'delete_existed':
            existed_anyfile.abspath.unlink()
            existed_anyfile.update_path(inserted_anyfile.directory, inserted_anyfile.filename)
        elif card_status == 'deleted' and what_do == 'delete':
            existed_anyfile.delete()
        else:
            return Response(status=status.HTTP_403_BAD_REQUEST)

        return Response(status=status.HTTP_204_NO_CONTENT)
