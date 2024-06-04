from abc import abstractmethod
from typing import Generic, TypeVar

from django.conf import settings
from django.core.cache import caches
from django.core.exceptions import ObjectDoesNotExist
from queryish import Queryish, VirtualModel

from . import campaign_backends


T = TypeVar("T", bound="AudienceBase")


class CachedApiQueryish(Queryish, Generic[T]):
    cache_prefix: str

    @abstractmethod
    def get_list(self) -> "dict[str, T]": ...

    def cache_key(self, pk):
        return f"{self.cache_prefix}{pk}"

    def get_instance(self, pk, **kwargs):
        return self.model(id=pk, **kwargs)  # type: ignore

    def parse_filters(self):
        return dict(self.filters)

    def get_detail(self, pk) -> T:
        instance = self.get_list().get(pk, None)
        if instance is None:
            raise self.model.DoesNotExist  # type: ignore
        return instance

    def run_query(self):
        cache = caches["default"]
        filters = self.parse_filters()
        if set(filters) == {"pk"}:
            pk = filters["pk"]
            cache_key = self.cache_key(pk)
            kwargs = cache.get(cache_key)
            if kwargs is None:
                kwargs = self.get_detail(pk).to_json()
                timeout = getattr(settings, "WAGTAIL_NEWSLETTER_CACHE_TIMEOUT", 300)
                cache.set(cache_key, kwargs, timeout)
            yield self.get_instance(pk, **kwargs)
            return

        if filters:
            raise RuntimeError(f"Filters not supported: {filters!r}")

        for pk, value in self.get_list().items():
            cache.set(self.cache_key(pk), value.to_json())
            yield value


class AudienceQuerySet(CachedApiQueryish):
    cache_prefix = "wagtail-newsletter-audience-"

    def get_list(self):
        return {
            audience.id: audience
            for audience in campaign_backends.get_backend().get_audiences()
        }


class AudienceSegmentQuerySet(CachedApiQueryish):
    cache_prefix = "wagtail-newsletter-audience-segment-"

    def parse_filters(self):
        filters = super().parse_filters()

        if "audience" in filters:
            self.audience_id = filters.pop("audience")
        elif "pk" in filters:
            self.audience_id = filters["pk"].split("/")[0]
        else:
            self.audience_id = None

        return filters

    def get_list(self):
        if self.audience_id is None:
            return {}

        backend = campaign_backends.get_backend()
        try:
            segments = backend.get_audience_segments(self.audience_id)
        except Audience.DoesNotExist:
            return {}

        else:
            return {segment.id: segment for segment in segments}


class AudienceBase(VirtualModel):
    pk: str
    id: str
    name: str
    member_count: int

    class Meta:
        fields = ["id", "name", "member_count"]

    def __str__(self):
        return self.name

    def __eq__(self, other):
        return type(self) is type(other) and self.id == other.id

    def to_json(self):
        return {
            "name": self.name,
            "member_count": self.member_count,
        }


class Audience(AudienceBase):
    base_query_class = AudienceQuerySet
    objects: AudienceQuerySet

    class DoesNotExist(ObjectDoesNotExist):
        pass


class AudienceSegment(AudienceBase):
    base_query_class = AudienceSegmentQuerySet
    objects: AudienceSegmentQuerySet

    class DoesNotExist(ObjectDoesNotExist):
        pass
