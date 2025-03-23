import os
import asyncio
import json
from pydantic import BaseModel, Field
from typing import List
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode, LLMConfig
from crawl4ai.extraction_strategy import LLMExtractionStrategy
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy
from crawl4ai.content_filter_strategy import BM25ContentFilter


async def main():
    schema = {
        "name": "农机补贴数据",
        "baseSelector": ".c-table tr",  # 根据实际表格结构调整选择器
        "fields": [
            {"name": "序号", "selector": "td:nth-child(1)", "type": "integer"},
            {"name": "县", "selector": "td:nth-child(2)", "type": "text"},
            {"name": "所在乡(镇)", "selector": "td:nth-child(3)", "type": "text"},
            {"name": "购机者姓名", "selector": "td:nth-child(4)", "type": "text"},
            {"name": "机具品目", "selector": "td:nth-child(5)", "type": "text"},
            {"name": "生产厂家", "selector": "td:nth-child(6)", "type": "text"},
            {"name": "产品名称", "selector": "td:nth-child(7)", "type": "text"},
            {"name": "购买机型", "selector": "td:nth-child(8)", "type": "text"},
            {"name": "购买数量(台)", "selector": "td:nth-child(9)", "type": "integer"},
            {"name": "经销商", "selector": "td:nth-child(10)", "type": "text"},
            {"name": "购机日期", "selector": "td:nth-child(11)", "type": "text"},
            {"name": "单台销售价格(元)", "selector": "td:nth-child(12)", "type": "float"},
            {"name": "单台中央补贴额(元)", "selector": "td:nth-child(13)", "type": "float"},
            {"name": "单台省级补贴额(元)", "selector": "td:nth-child(14)", "type": "float"},
            {"name": "总补贴额(元)", "selector": "td:nth-child(15)", "type": "float"},
            {"name": "出厂编号", "selector": "td:nth-child(16)", "type": "text"},
            {"name": "状态", "selector": "td:nth-child(17)", "type": "text"},
            {"name": "是否超录申请", "selector": "td:nth-child(18)", "type": "text"}
        ]
    }

    # llm_strategy = LLMExtractionStrategy(
    #     llm_config=LLMConfig(provider="deepseek/deepseek-chat", api_token="sk-349f0f8eb6e349a09721748f1a4c1b91"),
    #     extraction_type="schema",
    #     instruction="""
    #         主要关注网站中表单数据
    #         包括:
    #         - 表单中每行数据
    #         不包括:
    #         - 搜索栏中的数据
    #         Format the output as clean markdown with proper code blocks and headers.
    #         """,
    #     chunk_token_threshold=1000,
    #     overlap_rate=0.0,
    #     apply_chunking=True,
    #     input_format="markdown",  # or "html", "fit_markdown"
    #     extra_args={"temperature": 0.0, "max_tokens": 800}
    # )

    # crawl_config = CrawlerRunConfig(
    #     extraction_strategy=llm_strategy,
    #     cache_mode=CacheMode.BYPASS
    # )

    # 3. Create a browser config if needed
    browser_config = BrowserConfig(verbose=True, headless=True)

    md_llm_generator = DefaultMarkdownGenerator(
        content_filter=filter,
        options={"ignore_links": True})

    bm25_filter = BM25ContentFilter(
        user_query="machine learning",
        bm25_threshold=1.2,
    )

    md_generator = DefaultMarkdownGenerator(
        content_filter=bm25_filter,
        options={"ignore_links": True}
    )

    index_conf = CrawlerRunConfig(
        # extraction_strategy=llm_strategy,
        cache_mode=CacheMode.BYPASS,
        wait_for="css:.c-table"
    )

    async with AsyncWebCrawler(config=browser_config) as crawler:
        # 打开主页
        result = await crawler.arun(
            url="http://223.70.233.163:8080/GouZBT2021to2023/pub/gongshi",
            config=index_conf
        )

        print(result.markdown)  # Print clean markdown content

        js_commands = [
            "document.getElementById('YearNum').click();",
            "document.getElementById('YearNum').value = '2021';",
            """document.querySelector('button.custom-btn.primary[onclick*="GongShiSearchForm"]')?.click()"""
        ]

        year_2021_conf = CrawlerRunConfig(
            # extraction_strategy=llm_strategy,
            extraction_strategy=JsonCssExtractionStrategy(schema),
            markdown_generator=md_generator,
            cache_mode=CacheMode.BYPASS,
            css_selector=".c-table",
            excluded_tags=['divPage', 'span'],
            js_code=js_commands
        )

        # 选择2021年查询
        page_2021_result = await crawler.arun(
            url="http://223.70.233.163:8080/GouZBT2021to2023/pub/gongshi",
            config=year_2021_conf
        )
        print(page_2021_result.markdown)  # Print clean markdown content

        if page_2021_result.success:
            print("Extracted content:", page_2021_result.extracted_content)
        else:
            print("Error:", page_2021_result.error_message)

        # js_next_page = """
        #     const nextBtns = document.querySelectorAll('i.mdi-chevron-right');
        #     if (nextBtns.length > 0) {
        #         // 创建鼠标事件模拟真实点击
        #         const mouseEvent = new MouseEvent('click', {
        #             bubbles: true,
        #             cancelable: true,
        #             view: window
        #         });
        #
        #         // 点击最后一个右箭头按钮（通常为下一页）
        #         nextBtns[nextBtns.length - 1].dispatchEvent(mouseEvent);
        #     }"""
        #
        # next_page_conf = CrawlerRunConfig(
        #     # extraction_strategy=llm_strategy,
        #     extraction_strategy=JsonCssExtractionStrategy(schema),
        #     markdown_generator=md_generator,
        #     cache_mode=CacheMode.BYPASS,
        #     css_selector=".c-table",
        #     excluded_tags=['divPage', 'span'],
        #     js_code=js_next_page,
        #     wait_for="css:.c-table"
        # )
        #
        # result = await crawler.arun(
        #     url=page_2021_result.url,
        #     config=next_page_conf
        # )
        # # print(result.markdown)  # Print clean markdown content
        #
        # if result.success:
        #     print("Extracted content:", result.extracted_content)
        # else:
        #     print("Error:", result.error_message)

        # if result.success:
        #     # 5. The extracted content is presumably JSON
        #     data = json.loads(result.extracted_content)
        #     print("Extracted items:", data)
        #
        #     # 6. Show usage stats
        #     llm_strategy.show_usage()  # prints token usage
        # else:
        #     print("Error:", result.error_message)


if __name__ == "__main__":
    asyncio.run(main())
