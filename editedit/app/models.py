from django.db import models

from django.contrib.auth.models import User

class Page(models.Model):
   title = models.CharField(max_length=255, unique=True)
   created_at = models.DateTimeField(auto_now_add=True)
#    updated_at = models.DateTimeField(auto_now=True)  # Don't need this!
   def __str__(self):
       return self.title

class PageRevision(models.Model):
   page = models.ForeignKey(Page, on_delete=models.CASCADE, related_name='revisions')
   content = models.TextField()
   editor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
   edited_at = models.DateTimeField(auto_now_add=True)
   def __str__(self):
       return f"{self.page.title} - Revision {self.id}"

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    is_curator = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} ({'curator' if self.is_curator else 'harvester'})"