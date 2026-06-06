from modeltranslation.translator import TranslationOptions, register

from .models import Excursion, Flight, Hotel, HotelRoom, TourPackage, HotelFeature, HotelImage, Transfer



@register(Hotel)
class HotelTranslationOptions(TranslationOptions):
    fields = ('name', 'city', 'description')


@register(HotelRoom)
class HotelRoomTranslationOptions(TranslationOptions):
    fields = ('note',)


@register(HotelFeature)
class HotelFeatureTranslationOptions(TranslationOptions):
    fields = ('name',)


@register(Flight)
class FlightTranslationOptions(TranslationOptions):
    fields = ('origin', 'destination')


@register(TourPackage)
class TourPackageTranslationOptions(TranslationOptions):
    fields = ('name', 'destination')


@register(Excursion)
class ExcursionTranslationOptions(TranslationOptions):
    fields = ('name', 'city')


@register(Transfer)
class TransferTranslationOptions(TranslationOptions):
    fields = ('name', 'from_location', 'to_location', 'vehicle_type')
