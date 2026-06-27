from rest_framework import serializers, viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Applicant

class ApplicantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Applicant
        fields = ["id", "organization", "applicant_type", "full_name", "phone", "email", "address", "nin_masked", "bvn_masked", "status", "submitted_at"]
        read_only_fields = ["id", "nin_masked", "bvn_masked", "submitted_at"]

class ApplicantViewSet(viewsets.ModelViewSet):
    serializer_class = ApplicantSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Applicant.objects.select_related("organization").order_by("-submitted_at")
        if self.request.user.organization:
            queryset = queryset.filter(organization=self.request.user.organization)
        return queryset
