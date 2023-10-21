from django.contrib import admin
from .models import Category, NewAnek, Anek


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    ordering = ('id', 'name')


# Processing new jokes on the admin page
@admin.action(description='Добавить анекдот в БД')
def admin_anek_published(modeladmin, request, queryset):
    for new_anek in queryset:
        Anek.objects.create(text=new_anek.text, cat=new_anek.cat)
        new_anek.delete()


# Delete new jokes on the admin page
@admin.action(description='Удалить выбранные анекдоты из БД')
def admin_anek_delete(modeladmin, request, queryset):
    queryset.delete()


@admin.register(NewAnek)
class NewAnekAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'Category', 'text')
    ordering = ('id', 'user', 'cat', 'text')
    search_fields = ('user', 'cat')
    list_filter = ('user',)
    def Category(self, obj):
         return obj.cat.name if obj.cat else None
    actions =[admin_anek_published, admin_anek_delete]


@admin.register(Anek)
class AnekAdmin(admin.ModelAdmin):
    list_display = ('id', 'Category', 'text')
    ordering = ('id',)
    search_fields = ('text',)
    def Category(self, obj):
         return obj.cat.name if obj.cat else None

