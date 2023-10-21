from django.db import models
from django.contrib.auth.models import User



class Anek(models.Model):
    cat = models.ForeignKey('Category', models.DO_NOTHING, default=1)
    text = models.TextField()



class Category(models.Model):
    name = models.TextField()


class NewAnek(models.Model):
    user = models.ForeignKey(User, models.DO_NOTHING, blank=True, null=True)
    cat = models.ForeignKey(Category, models.DO_NOTHING, default=1)
    text = models.CharField(max_length=999, blank=True, null=True)


class Ratings(models.Model):
    anek = models.ForeignKey(Anek, models.DO_NOTHING, blank=True, null=True)
    user = models.ForeignKey(User, models.DO_NOTHING, blank=True, null=True)
    rating = models.IntegerField(blank=True, null=True)




