from django.db.models import ProtectedError

from rest_framework import status, viewsets
from rest_framework.response import Response

from accounts.api_permissions import IsAdminOrReadOnly

from .models import City
from .serializers import CitySerializer


class CityViewSet(viewsets.ModelViewSet):
    queryset = City.objects.all()
    serializer_class = CitySerializer
    permission_classes = [IsAdminOrReadOnly]

    def destroy(self, request, *args, **kwargs):
        city = self.get_object()

        try:
            city.delete()
        except ProtectedError:
            return Response(
                {
                    "detail": (
                        "This city cannot be deleted because "
                        "it is linked to existing sites or customers."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            status=status.HTTP_204_NO_CONTENT
        )