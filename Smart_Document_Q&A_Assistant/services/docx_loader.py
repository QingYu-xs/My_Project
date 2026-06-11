"""
纯标准库 .docx 文本提取器
.docx 文件本质是 ZIP 压缩包，内部包含 word/document.xml，
本模块通过 zipfile + xml.etree.ElementTree 直接解析 XML，
无需安装 python-docx 依赖。
"""
import zipfile
import xml.etree.ElementTree as ET

from langchain_core.documents import Document


class SimpleDocxLoader:
    """使用纯标准库解析 .docx 文件并提取文本"""

    def __init__(self, file_path: str):
        self.file_path = str(file_path)

    def load(self):
        """加载 .docx 文件，返回包含一个 Document 对象的列表"""
        text = self._extract_text()
        return [Document(page_content=text, metadata={"source": self.file_path})]

    def _extract_text(self) -> str:
        """从 word/document.xml 中提取所有段落文本"""
        paragraphs = []
        with zipfile.ZipFile(self.file_path) as z:
            xml_content = z.read("word/document.xml")           # 读取 XML 内容
            root = ET.fromstring(xml_content)

            # 遍历所有 <w:p>（段落）标签
            for para in root.iter(
                "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p"
            ):
                texts = []
                # 遍历段落中的 <w:r>（文本片段）标签
                for run in para.iter(
                    "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}r"
                ):
                    # 提取 <w:t>（文本内容）标签中的文字
                    for t in run.iter(
                        "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t"
                    ):
                        if t.text:
                            texts.append(t.text)
                if texts:
                    paragraphs.append("".join(texts))
        return "\n".join(paragraphs)


def get_docx_loader(file_path: str):
    """返回 SimpleDocxLoader 实例"""
    return SimpleDocxLoader(file_path)
