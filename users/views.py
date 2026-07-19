from .serializers import UserSerializers
from rest_framework.views import APIView
from rest_framework.response import Response


class UserView(APIView):
    def get(self, request):
        user = request.user
        serializer = UserSerializers(user)
        return Response(serializer.data)
