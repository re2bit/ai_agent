import time
import logging
from unittest import TestCase

from langchain_core.language_models.fake_chat_models import FakeListChatModel
from langchain_core.messages import BaseMessage
from langchain_core.outputs import ChatResult, ChatGeneration
from typing_extensions import override

from agent_server.ai.nodes.internet_archive.Filter import FilterNode
from agent_server.ai.nodes.internet_archive.Finder import FinderNode
from agent_server.ai.prompts.internet_archive import FinderPromptFactory, FilterPromptFactory
from agent_server.ai.states.internet_archive import InternetArchiveState

DATA_VALID:dict={
                "query": "Super Mario Bros 2 Manual",
                "results": [
                    "super-mario-bros-2-nes-spielanleitung",
                ],
                "cached_results": True,
                "filtered_results": [
                    "super-mario-bros-2-nes-spielanleitung"
                ],
                "metadata": {
                    "super-mario-bros-2-nes-spielanleitung": {
                        "metadata": {
                            "identifier": "super-mario-bros-2-nes-spielanleitung",
                            "mediatype": "texts",
                            "collection": ["manuals_various", "manuals", "additional_collections"],
                            "creator": "Nintendo", "date": "1989",
                            "description": "German instruction booklet for Super Mario Bros. 2 (NES)",
                            "language": "ger", "scanner": "Internet Archive HTML5 Uploader 1.6.4",
                            "subject": [
                                "Super Mario",
                                "Bros",
                                "Bros 2",
                                "german",
                                "deutsch",
                                "anleitung",
                                "gebrauchsanleitung",
                                "spielanleitung",
                                "spieleanleitung",
                                "manual",
                                "instruction",
                                "booklet"
                            ],
                            "title": "Super Mario Bros 2 - NES - Spielanleitung",
                            "uploader": "email8000@protonmail.com",
                            "publicdate": "2020-12-14 15:43:09",
                            "addeddate": "2020-12-14 15:43:09",
                            "curation": "[curator]validator@archive.org[/curator][date]20201214154927[/date][comment]checked for malware[/comment]",
                            "identifier-access": "http://archive.org/details/super-mario-bros-2-nes-spielanleitung",
                            "identifier-ark": "ark:/13960/t5n972m2p",
                            "ppi": "144",
                            "ocr": "tesseract 4.1.1",
                            "ocr_parameters": "-l deu",
                            "ocr_module_version": "0.0.9",
                            "ocr_detected_script": "Latin",
                            "ocr_detected_script_conf": "0.6934",
                            "ocr_detected_lang": "de",
                            "ocr_detected_lang_conf": "1.0000",
                            "pdf_module_version": "0.0.4", "coverleaf": "0"
                        },
                        "files": [
                            {
                                "name": "Super Mario Bros 2 - NES - Spielanleitung.epub",
                                "source": "derivative",
                                "original": "Super Mario Bros 2 - NES - Spielanleitung_hocr.html",
                                "mtime": "1704419608",
                                "size": "20782",
                                "md5": "4c7b6ed361435e673846d73866f8d386",
                                "crc32": "29c44d84",
                                "sha1": "eb81e55570688653cbc992642b8a8647eda1129c",
                                "format": "EPUB"
                            },
                            {
                                "name": "Super Mario Bros 2 - NES - Spielanleitung.pdf",
                                "source": "original",
                                "mtime": "1607960551",
                                "size": "4379827",
                                "md5": "d58478963225f9772df91584d97726cf",
                                "crc32": "f4ab069d",
                                "sha1": "dd5da93963bfee2f49ae8dc4438abd780460f5aa",
                                "format": "Image Container PDF"
                            },

                            {"name": "Super Mario Bros 2 - NES - Spielanleitung_chocr.html.gz",
                             "source": "derivative",
                             "format": "chOCR",
                             "original": "Super Mario Bros 2 - NES - Spielanleitung_jp2.zip",
                             "mtime": "1607961210",
                             "size": "273258",
                             "md5": "cea67d62416cdcc093444dbf8733fe85",
                             "crc32": "bfbf25cc",
                             "sha1": "57593144fd6a65963a25683f8bf642601198dae0"
                             },
                            {"name": "Super Mario Bros 2 - NES - Spielanleitung_djvu.txt", "source": "derivative",
                             "format": "DjVuTXT", "original": "Super Mario Bros 2 - NES - Spielanleitung_djvu.xml",
                             "mtime": "1607961231", "size": "21308", "md5": "891e5c15794a76ee7bf4375c3444e090",
                             "crc32": "9bc7c4d4", "sha1": "25a4856746dd483579d69aa9581b5284b4fd6c10"},

                            {"name": "Super Mario Bros 2 - NES - Spielanleitung_djvu.xml", "source": "derivative",
                             "format": "Djvu XML",
                             "original": "Super Mario Bros 2 - NES - Spielanleitung_chocr.html.gz",
                             "mtime": "1607961228", "size": "270220", "md5": "fc2b5b87955beba93c5c40dc101515f7",
                             "crc32": "0fc6fa33", "sha1": "8fff692dacf0329107193f0b23983018cae3f251"},

                            {"name": "Super Mario Bros 2 - NES - Spielanleitung_hocr.html", "source": "derivative",
                             "hocr_char_to_word_module_version": "1.0.0", "hocr_char_to_word_hocr_version": "1.1.2",
                             "format": "hOCR",
                             "original": "Super Mario Bros 2 - NES - Spielanleitung_chocr.html.gz",
                             "mtime": "1617515682", "size": "573105", "md5": "119e7510a5659cf59c012d4a9b372fe4",
                             "crc32": "17bc956e", "sha1": "98dfd6f6bc1b3831ba4d03e44d91bd25a831cf24"},

                            {"name": "Super Mario Bros 2 - NES - Spielanleitung_hocr_pageindex.json.gz",
                             "source": "derivative", "hocr_pageindex_module_version": "1.0.0",
                             "hocr_pageindex_hocr_version": "1.1.0", "format": "OCR Page Index",
                             "original": "Super Mario Bros 2 - NES - Spielanleitung_hocr.html",
                             "mtime": "1617515765",
                             "size": "226", "md5": "34494eb98d34221edc5ba99ee319bc8b", "crc32": "bae5a830",
                             "sha1": "d83427453f0cc7390970ef6a473914f9b41683a7"},

                            {"name": "Super Mario Bros 2 - NES - Spielanleitung_hocr_searchtext.txt.gz",
                             "source": "derivative", "hocr_fts_text_module_version": "1.1.0",
                             "hocr_fts_text_hocr_version": "1.1.0", "word_conf_0_10": "28", "word_conf_11_20": "16",
                             "word_conf_21_30": "27", "word_conf_31_40": "31", "word_conf_41_50": "34",
                             "word_conf_51_60": "35", "word_conf_61_70": "49", "word_conf_71_80": "90",
                             "word_conf_81_90": "309", "word_conf_91_100": "2464", "format": "OCR Search Text",
                             "original": "Super Mario Bros 2 - NES - Spielanleitung_hocr.html",
                             "mtime": "1617515854",
                             "size": "8383", "md5": "01092f902124f26b2d4e4ae9dfafe510", "crc32": "6165896a",
                             "sha1": "e99bff8316a044b78e60710a1246870c2975020f"},

                            {"name": "Super Mario Bros 2 - NES - Spielanleitung_jp2.zip", "source": "derivative",
                             "format": "Single Page Processed JP2 ZIP",
                             "original": "Super Mario Bros 2 - NES - Spielanleitung.pdf", "mtime": "1607961078",
                             "size": "1640639", "md5": "846426615faf33e9257e568ffa922c9f", "crc32": "1b81034e",
                             "sha1": "92ef3904ca5e32922e7654240f24ddab917344fc", "filecount": "18"},

                            {"name": "Super Mario Bros 2 - NES - Spielanleitung_page_numbers.json",
                             "source": "derivative",
                             "format": "Page Numbers JSON",
                             "original": "Super Mario Bros 2 - NES - Spielanleitung_djvu.xml",
                             "mtime": "1607961252",
                             "size": "3151", "md5": "d052abef720a785e4a7b0d4a5da12dd5", "crc32": "fe6c3048",
                             "sha1": "38b041575b87c5476b8e867e793743c9f4d8f932"},

                            {"name": "Super Mario Bros 2 - NES - Spielanleitung_scandata.xml", "source": "original",
                             "mtime": "1609721342", "size": "5959", "md5": "e88e2800efd263a2a25f00a434ba4008",
                             "crc32": "21e889a9", "sha1": "d69f89b5122e7d939488f9b1b15075a14b719b8a",
                             "format": "Scandata"},

                            {"name": "Super Mario Bros 2 - NES - Spielanleitung_text.pdf", "source": "derivative",
                             "format": "Additional Text PDF",
                             "original": "Super Mario Bros 2 - NES - Spielanleitung_page_numbers.json",
                             "mtime": "1607961347", "size": "764250", "md5": "8c772fcc917bf151c90e54c9f4f05b48",
                             "crc32": "0fd2a311", "sha1": "7afb26d1d0bebf83c13a8cac39832060c0734807"},

                            {"name": "__ia_thumb.jpg", "source": "original", "mtime": "1692504896", "size": "13144",
                             "md5": "baafac841cd133e96549a153f8409530", "crc32": "5a53cb22",
                             "sha1": "6f15ca0171195f8244df6326bbbf79bb2d24a64d", "format": "Item Tile",
                             "rotation": "0"},

                            {"name": "history/files/Super Mario Bros 2 - NES - Spielanleitung_scandata.xml.~1~",
                             "source": "derivative", "format": "Scandata",
                             "original": "Super Mario Bros 2 - NES - Spielanleitung_djvu.xml",
                             "mtime": "1607961248",
                             "size": "5959", "md5": "c4209f8491a5bcab3ca4c4ac3310af75", "crc32": "65f59adf",
                             "sha1": "74d2c73cb0a928d88d846600cdc4c1b271ad55e2", "old_version": "true"},

                            {"name": "super-mario-bros-2-nes-spielanleitung_archive.torrent", "source": "metadata",
                             "btih": "d4254c68346f510c80433808aebc491d010c2705", "mtime": "1704419610",
                             "size": "4887",
                             "md5": "6a7dee6ab48f37b508b5adb100abafe2", "crc32": "67ab021e",
                             "sha1": "8d7d03e9b26b7e159456f15bffb0eb29f81a4472", "format": "Archive BitTorrent"},

                            {"name": "super-mario-bros-2-nes-spielanleitung_files.xml", "source": "original",
                             "format": "Metadata", "md5": "bb676f61e2cb668d5bd0009176db4c43", "summation": "md5"},

                            {"name": "super-mario-bros-2-nes-spielanleitung_meta.sqlite", "source": "original",
                             "mtime": "1609721347", "size": "12288", "md5": "27505e4bb10e0f0fbd505bbf8f36622d",
                             "crc32": "a5a8f221", "sha1": "a6e77f9a7e58b451a9ffe5e20694da37709b3f6f",
                             "format": "Metadata"},

                            {"name": "super-mario-bros-2-nes-spielanleitung_meta.xml", "source": "original",
                             "mtime": "1692504895", "size": "1804", "md5": "990dc4f8e42b9c158535921764c22124",
                             "crc32": "8ae26397", "sha1": "2c13aa3077757fda3192b3d23b253ffc20c47974",
                             "format": "Metadata"}
                        ]
                    }
                },
                "error": None
            }

class FakeListAndRespChatModel(FakeListChatModel):
    received_messages: list[BaseMessage] | None = None

    @override
    def _generate(
            self,
            **data,
    ) -> ChatResult:
        self.received_messages = data.get("messages") or None
        if self.sleep is not None:
            time.sleep(self.sleep)
        response = self.responses[self.i]
        if self.i < len(self.responses) - 1:
            self.i += 1
        else:
            self.i = 0
        generation = ChatGeneration(message=response)
        return ChatResult(generations=[generation])

    def get_received_messages(self) -> list[BaseMessage] | None:
        return self.received_messages


class TestFindNode(TestCase):
    response: list[str] = [
        "{\"is_this_entry_relevant\":true}"
    ]

    def test_failed_instantiate(self):
        try:
            FinderNode(
                llm=None,
                logger=None,
                prompt_factory=None
            )
            assert False
        except Exception:
            assert True

    def test_instantiate(self):
        llm = FakeListChatModel(responses=self.response)
        finder: FinderNode = FinderNode(
            llm=llm,
            logger=None,
            prompt_factory=None
        )
        assert finder.__class__.__name__ == "FinderNode"

    def test_invoke_valid_results(self):
        logger = logging.getLogger(__name__)
        prompt_factory = FinderPromptFactory
        llm = FakeListChatModel(responses=self.response)
        finder = FinderNode(
            llm=llm,
            logger=logger,
            prompt_factory=prompt_factory
        )
        state = InternetArchiveState(**DATA_VALID)
        with self.assertLogs(logger, level=logging.INFO) as cm:
            result = finder.invoke(state=state)
        error = result.get("error") or ""
        assert error is ""
        entries_to_consider = result.get("entries_to_consider") or None
        assert entries_to_consider is not None
        assert "super-mario-bros-2-nes-spielanleitung" in entries_to_consider


class TestFilterNode(TestCase):
    response: list[str] = [
        "{\"filtered_results\":[\"super-mario-bros-2-nes-spielanleitung\"]}"
    ]

    def test_failed_instantiate(self):
        try:
            FilterNode(
                llm=None,
                prompt_factory=None,
                logger=None,
            )
            assert False
        except Exception:
            assert True

    def test_instantiate(self):
        llm = FakeListChatModel(responses=self.response)
        node: FilterNode = FilterNode(
            llm=llm,
            prompt_factory=FilterPromptFactory,
            logger=None,
        )
        assert node.__class__.__name__ == "FilterNode"

    def test_invoke_valid_results(self):
        logger = logging.getLogger(__name__)
        prompt_factory = FilterPromptFactory
        llm = FakeListChatModel(responses=self.response)
        node = FilterNode(
            llm=llm,
            prompt_factory=prompt_factory,
            logger=logger,
        )
        state = InternetArchiveState(**DATA_VALID)
        with self.assertLogs(logger, level=logging.INFO) as cm:
            result = node.invoke(state=state)
        error = result.get("error") or ""
        assert error is ""
        filtered_results = result.get("filtered_results") or None
        assert filtered_results is not None
        assert "super-mario-bros-2-nes-spielanleitung" in filtered_results