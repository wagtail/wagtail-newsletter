from wagtail import blocks
from wagtail.images.blocks import ImageChooserBlock


class ImageBlock(blocks.StructBlock):
    image = ImageChooserBlock()
    caption = blocks.CharBlock(required=False)

    class Meta:  # type: ignore
        template = "blocks/image_block.html"


class StoryBlock(blocks.StreamBlock):
    rich_text = blocks.RichTextBlock()
    image = ImageBlock()
    raw_html = blocks.RawHTMLBlock()
