from wagtail import blocks
from wagtail.images.blocks import ImageChooserBlock


class ImageBlock(blocks.StructBlock):
    image = ImageChooserBlock()
    caption = blocks.CharBlock(required=False)

    class Meta:  # type: ignore
        template = "blocks/image_block.html"


def is_rendering_newsletter(context):
    return bool((context or {}).get("rendering_newsletter"))


class WebOnlyBlock(blocks.RichTextBlock):
    def render(self, value, context=None):
        if is_rendering_newsletter(context):
            return ""

        return super().render(value, context)


class EmailOnlyBlock(blocks.RichTextBlock):
    def render(self, value, context=None):
        if not is_rendering_newsletter(context):
            return ""

        return super().render(value, context)


class StoryBlock(blocks.StreamBlock):
    rich_text = blocks.RichTextBlock()
    image = ImageBlock()
    raw_html = blocks.RawHTMLBlock()
    email_only = EmailOnlyBlock(group="Channel")
    web_only = WebOnlyBlock(group="Channel")
