from cms import settings
from django.contrib import admin
from django.forms.models import model_to_dict, fields_for_model, save_instance
from cms.utils import get_language_from_request

"""
Example usage:

models.py

from django.db import models
from cms.models.modelwithplugins import ModelWithPlugins
from cms import settings

class BlogEntry(ModelWithPlugins):
    published = models.BooleanField()

class Title(models.Model): 
    entry = models.ForeignKey(BlogEntry)
    language = models.CharField(max_length=2, choices=settings.LANGUAGES)
    title = models.CharField(max_length=255)
    slug = models.SlugField()

admin.py

from django.contrib import admin
from cms.translation.admin import PluginTranslationAdmin
from models import BlogEntry, Title

class BlogEntryAdmin(PluginTranslationAdmin):

    translation_model = Title
    translation_model_fk = 'entry'
    placeholders = ['main']

admin.site.register(BlogEntry, BlogEntryAdmin)
"""

def get_translation_admin(admin_base):
    
    class RealTranslationAdmin(admin_base):
    
        translation_model = None
        translation_model_fk = ''
        translation_model_language = 'language'

        change_list_template = 'admin/apply_change_list.html'

        list_display = ('languages',)
    
        def languages(self, obj, extra):
          return ' '.join(['<a href="%s/?language=%s">%s</a>' % (obj.pk, t.language, t.language.upper()) for t in extra['translations']])
        languages.short_description = 'Languages'
        languages.allow_tags = True
        languages.takes_extra = True
        
        def add_extra_to_results(self, results, request):
            
            if hasattr(super(RealTranslationAdmin, self), 'add_extra_to_results'):
                extras = super(RealTranslationAdmin, self).add_extra_to_results(results, request)
            else:
                extras = [{} for r in results]
            
            results = list(results)
            id_list = [r.pk for r in results]
            pk_index_map = dict([(pk, index) for index, pk in enumerate(id_list)])
            
            model = self.translation_model
            translations = model.objects.filter(**{
                self.translation_model_fk + '__in': id_list
            })
            
            for obj in translations:
                index = pk_index_map[getattr(obj, self.translation_model_fk + '_id')]
                if not 'translations' in extras[index]:
                    extras[index]['translations'] = []
                extras[index]['translations'].append(obj)
            
            return extras
            
        def get_translation(self, request, obj):
    
            language = get_language_from_request(request)
    
            if obj:
    
    
                get_kwargs = {
                    self.translation_model_fk: obj,
                    self.translation_model_language: language
                }
    
                try:
                    return self.translation_model.objects.get(**get_kwargs)
                except:
                    return self.translation_model(**get_kwargs)
    
            return self.translation_model(**{self.translation_model_language: language})
    
        def get_form(self, request, obj=None, **kwargs):
    
            form = super(RealTranslationAdmin, self).get_form(request, obj, **kwargs)
    
            add_fields = fields_for_model(self.translation_model, exclude=[self.translation_model_fk])
    
            translation_obj = self.get_translation(request, obj)
            initial = model_to_dict(translation_obj)
    
            for name, field in add_fields.items():
                form.base_fields[name] = field
                if name in initial:
                    form.base_fields[name].initial = initial[name]
    
            return form
    
    
        def save_model(self, request, obj, form, change):
    
            super(RealTranslationAdmin, self).save_model(request, obj, form, change)
                
            translation_obj = self.get_translation(request, obj)
    
            new_translation_obj = save_instance(form, translation_obj, commit=False)
    
            setattr(new_translation_obj, self.translation_model_fk, obj)
    
            new_translation_obj.save()
            
    return RealTranslationAdmin

from cms.admin.pluginadmin import PluginAdmin

TranslationAdmin = get_translation_admin(admin.ModelAdmin)

TranslationPluginAdmin = get_translation_admin(PluginAdmin)

if 'reversion' in settings.INSTALLED_APPS:
    
    from reversion.admin import VersionAdmin    
    from cms.admin.pluginadmin import PluginVersionAdmin
    
    TranslationVersionAdmin = get_translation_admin(VersionAdmin)
    
    TranslationPluginVersionAdmin = get_translation_admin(PluginVersionAdmin) 