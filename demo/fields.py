import json

from wagtail.fields import StreamField as WagtailStreamfield


class StreamField(WagtailStreamfield):
    def __init__(self, *args, **kwargs):
        """
        Overrides StreamField.__init__() to account for `block_types` no longer
        being received as an arg when migrating (because there is no longer a
        `block_types` value in the migration to provide).
        """
        if args:
            block_types = args[0] or []
            args = args[1:]
        else:
            block_types = kwargs.pop("block_types", [])
        super().__init__(block_types, *args, **kwargs)

    def deconstruct(self):
        """
        Overrides StreamField.deconstruct() to remove `block_types` and
        `verbose_name` values so that migrations remain smaller in size,
        and changes to those attributes do not require a new migration.
        """
        name, path, args, kwargs = super().deconstruct()
        if args:
            args = args[1:]
        else:
            kwargs.pop("block_types", None)
        kwargs.pop("verbose_name", None)
        return name, path, args, kwargs

    def to_python(self, value):
        """
        Overrides StreamField.to_python() to make the return value
        (a `StreamValue`) more useful when migrating. When migrating, block
        definitions are unavailable to the field's underlying StreamBlock,
        causing self.stream_block.to_python() to not recognise any of the
        blocks in the stored value.
        """
        stream_value = super().to_python(value)

        # There is no way to be absolutely sure this is a migration,
        # but the combination of factors below is a pretty decent indicator
        if not self.stream_block.child_blocks and value and not stream_value._raw_data:  # type: ignore
            stream_data = None
            if isinstance(value, list):
                stream_data = value
            elif isinstance(value, str):
                try:
                    stream_data = json.loads(value)
                except ValueError:
                    stream_value.raw_text = value  # type: ignore

            if stream_data:
                return type(stream_value)(self, stream_data, is_lazy=True)  # type: ignore

        return stream_value
