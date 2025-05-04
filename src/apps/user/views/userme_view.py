from rest_framework.generics import RetrieveUpdateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from apps.user.models import User
from apps.user.serializers.userme_serializer import UserMeSerializer


class UserMeView(RetrieveUpdateAPIView):
    """
    UserMeView is a view that allows authenticated users to retrieve and update their own user information.
    """

    serializer_class = UserMeSerializer
    permission_classes = [IsAuthenticated]
    queryset = User.objects.all()

    def get_object(self):
        return self.request.user

    def put(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

