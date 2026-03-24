from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
    """
    Gives each Django auth User a role (harvester or curator).
    """
    HARVESTER = "harvester"
    CURATOR = "curator"
    ROLE_CHOICES = [
        (HARVESTER, "Harvester"),
        (CURATOR, "Curator"),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    is_curator = models.BooleanField(default=False)

    def __str__(self) -> str:
        role = "curator" if self.is_curator else "harvester"
        return f"{self.user.username} ({role})"



class Institution(models.Model):
    """
    A school/institution we store facts for.
    """
    name = models.CharField(max_length=255, unique=True)

    def __str__(self) -> str:
        return self.name


class ReportingYear(models.Model):
    """
    A reporting year label like '2024-25'.
    """
    label = models.CharField(max_length=20, unique=True)

    def __str__(self) -> str:
        return self.label


class Upload(models.Model):
    """
    An uploaded CSV file from a harvester, tied to one institution and one reporting year.
    """
    uploader = models.ForeignKey(User, on_delete=models.PROTECT, related_name="uploads")
    institution = models.ForeignKey(Institution, on_delete=models.PROTECT, related_name="uploads")
    reporting_year = models.ForeignKey(ReportingYear, on_delete=models.PROTECT, related_name="uploads")

    url = models.URLField(blank=True, null=True)
    uploaded_file = models.FileField(upload_to="uploads/")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"Upload {self.id} ({self.institution} / {self.reporting_year})"


class FieldKey(models.Model):
    """
    The 'KEY' column values (i.e., which fact/field this row refers to).
    """
    key = models.CharField(max_length=255, unique=True)

    def __str__(self) -> str:
        return self.key


class Fact(models.Model):
    """
    The current value for a (Institution, ReportingYear, FieldKey).
    We keep "current_value" here for fast reads, and store full history in FactRevision.
    """
    institution = models.ForeignKey(Institution, on_delete=models.PROTECT, related_name="facts")
    reporting_year = models.ForeignKey(ReportingYear, on_delete=models.PROTECT, related_name="facts")
    field = models.ForeignKey(FieldKey, on_delete=models.PROTECT, related_name="facts")

    current_value = models.TextField(blank=True, null=True)

    # audit of the *current* value
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="facts_updated",
    )

    class Meta:
        unique_together = ("institution", "reporting_year", "field")

    def __str__(self) -> str:
        return f"{self.institution} {self.reporting_year}: {self.field.key}"


class FactRevision(models.Model):
    """
    Full history of every value ever set for a Fact, including when, who, and what upload it came from.
    """
    fact = models.ForeignKey(Fact, on_delete=models.CASCADE, related_name="revisions")

    value = models.TextField()

    # auditing / provenance
    source_upload = models.ForeignKey(
        Upload,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="fact_revisions",
    )
    changed_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="fact_revisions_made",
    )
    changed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"Revision {self.id} of Fact {self.fact_id}"
