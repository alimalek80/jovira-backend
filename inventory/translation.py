from modeltranslation.translator import TranslationOptions, register

from .models import Excursion, Flight, Hotel, TourPackage


@register(Hotel)
class HotelTranslationOptions(TranslationOptions):
    fields = ('name', 'city')


@register(Flight)
class FlightTranslationOptions(TranslationOptions):
    fields = ('origin', 'destination')


@register(TourPackage)
class TourPackageTranslationOptions(TranslationOptions):
    fields = ('name', 'destination')


@register(Excursion)
class ExcursionTranslationOptions(TranslationOptions):
    fields = ('name', 'city')
