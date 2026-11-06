import unittest

from textnode import TextNode, TextType
from inline_markdown import (
    split_nodes_delimiter, extract_markdown_images, extract_markdown_links,
    split_nodes_image, split_nodes_link, text_to_textnodes
)


class TestSplitNodesDelimiter(unittest.TestCase):
    # --- basic cases, one per delimiter type ---

    def test_code(self):
        node = TextNode("This is text with a `code block` word", TextType.TEXT)
        result = split_nodes_delimiter([node], "`", TextType.CODE)
        self.assertEqual(
            result,
            [
                TextNode("This is text with a ", TextType.TEXT),
                TextNode("code block", TextType.CODE),
                TextNode(" word", TextType.TEXT),
            ],
        )

    def test_bold(self):
        node = TextNode("This is **bold** text", TextType.TEXT)
        result = split_nodes_delimiter([node], "**", TextType.BOLD)
        self.assertEqual(
            result,
            [
                TextNode("This is ", TextType.TEXT),
                TextNode("bold", TextType.BOLD),
                TextNode(" text", TextType.TEXT),
            ],
        )

    def test_italic(self):
        node = TextNode("An _italic_ word", TextType.TEXT)
        result = split_nodes_delimiter([node], "_", TextType.ITALIC)
        self.assertEqual(
            result,
            [
                TextNode("An ", TextType.TEXT),
                TextNode("italic", TextType.ITALIC),
                TextNode(" word", TextType.TEXT),
            ]
        )

    # --- edge cases ---

    def test_multiple_delimited_sectioins(self):
        node = TextNode("**one** and **two**", TextType.TEXT)
        result = split_nodes_delimiter([node], "**", TextType.BOLD)
        self.assertEqual(
            result,
            [
                TextNode("one", TextType.BOLD),
                TextNode(" and ", TextType.TEXT),
                TextNode("two", TextType.BOLD),
            ],
        )

    def test_delimiter_at_start(self):
        node = TextNode("`code` at the start", TextType.TEXT)
        result = split_nodes_delimiter([node], "`", TextType.CODE)
        self.assertEqual(
            result,
            [
                TextNode("code", TextType.CODE),
                TextNode(" at the start", TextType.TEXT),
            ],
        )


    # --- errors ---

    def test_unmatched_delimiter_raises(self):
        node = TextNode("This is **broken", TextType.TEXT)
        with self.assertRaises(ValueError):
            split_nodes_delimiter([node], "**", TextType.BOLD)
    

    # --- non-text nodes and chaining --- 
    def test_non_text_nodes_unchanged(self):
        nodes = [TextNode("already **bold**", TextType.BOLD)]
        result = split_nodes_delimiter(nodes, "**", TextType.BOLD)
        self.assertEqual(result, nodes)

    def test_chaining_bold_then_italic(self):
        nodes = [TextNode("**bold** and _italic_", TextType.TEXT)]
        nodes = split_nodes_delimiter(nodes, "**", TextType.BOLD)
        nodes = split_nodes_delimiter(nodes, "_", TextType.ITALIC)
        self.assertEqual(
            nodes,
            [
                TextNode("bold", TextType.BOLD),
                TextNode(" and ", TextType.TEXT),
                TextNode("italic", TextType.ITALIC),
            ],
        )

    def test_code_is_not_split_again(self):
        nodes = [TextNode("`a ** b`", TextType.TEXT)]
        nodes = split_nodes_delimiter(nodes, "`", TextType.CODE)
        nodes = split_nodes_delimiter(nodes, "**", TextType.BOLD)
        self.assertEqual(nodes, [TextNode("a ** b", TextType.CODE)])

    # --- images ---

    def test_extract_markdown_images(self):
        matches = extract_markdown_images(
            "This is text with an ![image](https://i.imgur.com/zjjcJKZ.png)"
        )
        self.assertListEqual([("image", "https://i.imgur.com/zjjcJKZ.png")], matches)

    def test_extract_multiple_images(self):
        matches = extract_markdown_images(
            "A ![rick roll](https://i.imgur.com/aKaOqIh.gif) and "
            "![obi wan](https://i.imgur.com/fJRm4Vk.jpeg)"
        )
        self.assertListEqual(
            [
                ("rick roll", "https://i.imgur.com/aKaOqIh.gif"),
                ("obi wan", "https://i.imgur.com/fJRm4Vk.jpeg"),
            ],
            matches,
        )

    def test_extract_images_none(self):
        matches = extract_markdown_images("No images here, just text.")
        self.assertListEqual([], matches)

    def test_extract_image_empty_alt(self):
        matches = extract_markdown_images("![](https://example.com/pic.png)")
        self.assertListEqual([("", "https://example.com/pic.png")], matches)

    def test_extract_images_ignores_links(self):
        matches = extract_markdown_images(
            "A [link](https://www.boot.dev) and an ![image](https://example.com/a.png)"
        )
        self.assertListEqual([("image", "https://example.com/a.png")], matches)

    # --- links ---

    def test_extract_link(self):
        matches = extract_markdown_links(
            "This is a link [to boot dev](https://www.boot.dev)"
        )
        self.assertListEqual([("to boot dev", "https://www.boot.dev")], matches)

    def test_extract_multiple_links(self):
        matches = extract_markdown_links(
            "Links [to boot dev](https://www.boot.dev) and"
            "[to youtube](https://www.youtube.com/@bootdotdev)"
        )
        self.assertListEqual(
            [
                ("to boot dev", "https://www.boot.dev"),
                ("to youtube", "https://www.youtube.com/@bootdotdev"),
            ],
            matches,
        )

    def test_extract_links_none(self):
        matches = extract_markdown_links("No links here, just text.")
        self.assertListEqual([], matches)

    def test_extract_links_ignore_images(self):
        matches = extract_markdown_links(
            "An ![image](https://example.com/a.png) and a [link](https://www.boot.dev)"
        )
        self.assertListEqual([("link", "https://www.boot.dev")], matches)

    # --- images --- 

    def test_split_images(self):
        node = TextNode(
            "This is text with an ![image](https://i.imgur.com/zjjcJKZ.png) and another ![second image](https://i.imgur.com/3elNhQu.png)",
            TextType.TEXT,
        )
        new_nodes = split_nodes_image([node])
        self.assertListEqual(
            [
                TextNode("This is text with an ", TextType.TEXT),
                TextNode("image", TextType.IMAGE, "https://i.imgur.com/zjjcJKZ.png"),
                TextNode(" and another ", TextType.TEXT),
                TextNode("second image", TextType.IMAGE, "https://i.imgur.com/3elNhQu.png"),
            ],
            new_nodes,
        )

    def test_split_image_at_start(self):
        node = TextNode("![logo](https://example.com/logo.png) Welcome!", TextType.TEXT)
        self.assertListEqual(
            [
                TextNode("logo", TextType.IMAGE, "https://example.com/logo.png"),
                TextNode(" Welcome!", TextType.TEXT),
            ],
            split_nodes_image([node]),
        )

    def test_split_image_with_trailing_text(self):
        node = TextNode("Look at ![cat](https://example.com/cat.png) here", TextType.TEXT)
        self.assertListEqual(
            [
                TextNode("Look at ", TextType.TEXT),
                TextNode("cat", TextType.IMAGE, "https://example.com/cat.png"),
                TextNode(" here", TextType.TEXT),
            ],
            split_nodes_image([node]),
        )

    def test_split_image_only(self):
        node = TextNode("![only](https://example.com/only.png)", TextType.TEXT)
        self.assertListEqual(
            [TextNode("only", TextType.IMAGE, "https://example.com/only.png")],
            split_nodes_image([node]),
        )

    def test_split_images_none(self):
        node = TextNode("Just plain text", TextType.TEXT)
        self.assertListEqual([node], split_nodes_image([node]))

    def test_split_images_non_text_unchanged(self):
        node = TextNode("bold words", TextType.BOLD)
        self.assertListEqual([node], split_nodes_image([node]))

    def test_split_images_multiple_input_nodes(self):
        nodes = [
            TextNode("A ![x](https://example.com/x.png)", TextType.TEXT),
            TextNode("plain", TextType.TEXT),
        ]
        self.assertListEqual(
            [
                TextNode("A ", TextType.TEXT),
                TextNode("x", TextType.IMAGE, "https://example.com/x.png"),
                TextNode("plain", TextType.TEXT),
            ],
            split_nodes_image(nodes),
        )

    def test_split_images_same_image_twice(self):
        node = TextNode(
            "![a](https://example.com/a.png) and ![a](https://example.com/a.png)",
            TextType.TEXT,
        )
        self.assertListEqual(
            [
                TextNode("a", TextType.IMAGE, "https://example.com/a.png"),
                TextNode(" and ", TextType.TEXT),
                TextNode("a", TextType.IMAGE, "https://example.com/a.png"),
            ],
            split_nodes_image([node]),
        )

    def test_split_images_ignores_links(self):
        node = TextNode(
            "A [link](https://www.boot.dev) and ![img](https://example.com/i.png)",
            TextType.TEXT,
        )
        self.assertListEqual(
            [
                TextNode("A [link](https://www.boot.dev) and ", TextType.TEXT),
                TextNode("img", TextType.IMAGE, "https://example.com/i.png"),
            ],
            split_nodes_image([node]),
        )

    # --- links ---

    def test_split_links(self):
        node = TextNode(
            "This is text with a link [to boot dev](https://www.boot.dev) and [to youtube](https://www.youtube.com/@bootdotdev)",
            TextType.TEXT,
        )
        self.assertListEqual(
            [
                TextNode("This is text with a link ", TextType.TEXT),
                TextNode("to boot dev", TextType.LINK, "https://www.boot.dev"),
                TextNode(" and ", TextType.TEXT),
                TextNode("to youtube", TextType.LINK, "https://www.youtube.com/@bootdotdev"),
            ],
            split_nodes_link([node]),
        )

    def test_split_link_with_trailing_text(self):
        node = TextNode("Go [here](https://www.boot.dev) now", TextType.TEXT)
        self.assertListEqual(
            [
                TextNode("Go ", TextType.TEXT),
                TextNode("here", TextType.LINK, "https://www.boot.dev"),
                TextNode(" now", TextType.TEXT),
            ],
            split_nodes_link([node]),
        )

    def test_split_links_none(self):
        node = TextNode("Just plain text", TextType.TEXT)
        self.assertListEqual([node], split_nodes_link([node]))

    def test_split_links_non_text_unchanged(self):
        node = TextNode("some code", TextType.CODE)
        self.assertListEqual([node], split_nodes_link([node]))

    def test_split_links_ignores_images(self):
        node = TextNode(
            "An ![img](https://example.com/i.png) and a [link](https://www.boot.dev)",
            TextType.TEXT,
        )
        self.assertListEqual(
            [
                TextNode("An ![img](https://example.com/i.png) and a ", TextType.TEXT),
                TextNode("link", TextType.LINK, "https://www.boot.dev"),
            ],
            split_nodes_link([node]),
        )

    # --- both together ---

    def test_split_images_then_links(self):
        node = TextNode(
            "![img](https://example.com/i.png) then [link](https://www.boot.dev)",
            TextType.TEXT,
        )
        nodes = split_nodes_image([node])
        nodes = split_nodes_link(nodes)
        self.assertListEqual(
            [
                TextNode("img", TextType.IMAGE, "https://example.com/i.png"),
                TextNode(" then ", TextType.TEXT),
                TextNode("link", TextType.LINK, "https://www.boot.dev"),
            ],
            nodes,
        )

    def test_text_to_textnodes_full_example(self):
        text = (
            "This is **text** with an _italic_ word and a `code block` and an "
            "![obi wan image](https://i.imgur.com/fJRm4Vk.jpeg) and a [link](https://boot.dev)"
        )
        self.assertListEqual(
            [
                TextNode("This is ", TextType.TEXT),
                TextNode("text", TextType.BOLD),
                TextNode(" with an ", TextType.TEXT),
                TextNode("italic", TextType.ITALIC),
                TextNode(" word and a ", TextType.TEXT),
                TextNode("code block", TextType.CODE),
                TextNode(" and an ", TextType.TEXT),
                TextNode("obi wan image", TextType.IMAGE, "https://i.imgur.com/fJRm4Vk.jpeg"),
                TextNode(" and a ", TextType.TEXT),
                TextNode("link", TextType.LINK, "https://boot.dev"),
            ],
            text_to_textnodes(text),
        )

    def test_text_to_textnodes_plain(self):
        self.assertListEqual(
            [TextNode("Just plain text", TextType.TEXT)],
            text_to_textnodes("Just plain text"),
        )

    def test_text_to_textnodes_only_bold(self):
        self.assertListEqual(
            [TextNode("bold", TextType.BOLD)],
            text_to_textnodes("**bold**"),
        )

    def test_text_to_textnodes_adjacent_formatting(self):
        self.assertListEqual(
            [
                TextNode("bold", TextType.BOLD),
                TextNode("italic", TextType.ITALIC),
            ],
            text_to_textnodes("**bold**_italic_"),
        )

    def test_text_to_textnodes_image_first(self):
        self.assertListEqual(
            [
                TextNode("img", TextType.IMAGE, "https://example.com/i.png"),
                TextNode(" and ", TextType.TEXT),
                TextNode("bold", TextType.BOLD),
            ],
            text_to_textnodes("![img](https://example.com/i.png) and **bold**"),
        )

    

    def test_text_to_textnodes_underscore_in_url(self):
        self.assertListEqual(
            [
                TextNode("See ", TextType.TEXT),
                TextNode("my page", TextType.LINK, "https://example.com/my_page"),
                TextNode(" now", TextType.TEXT),
            ],
            text_to_textnodes("See [my page](https://example.com/my_page) now"),
        )

    def test_text_to_textnodes_unmatched_raises(self):
        with self.assertRaises(ValueError):
            text_to_textnodes("This is **broken")

    def test_text_to_textnodes_empty(self):
        self.assertListEqual([], text_to_textnodes(""))


if __name__ == "__main__":
    unittest.main()

