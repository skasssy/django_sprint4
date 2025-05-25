from django.contrib import admin
from .models import Category, Location, Post


# Register your models here.
class CategoryAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'is_published'
    )
    list_editable = ('is_published',)
    search_fields = ('title',)


class LocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_published')
    list_editable = ('is_published',)
    search_fields = ('name',)


class PostAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'pub_date',
        'author',
        'location',
        'category',
        'is_published'
    )
    list_editable = ('is_published',)
    search_fields = ('title', 'text')
    list_filter = ('category', 'location', 'pub_date')
    date_hierarchy = 'pub_date'


admin.site.register(Post, PostAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Location, LocationAdmin)

admin.site.empty_value_display = 'Не задано'
