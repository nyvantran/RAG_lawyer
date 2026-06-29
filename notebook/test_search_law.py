import os
import sys

# Thêm thư mục gốc của project vào sys.path để python có thể tìm thấy package `app`
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.tool import SearchLawTool


def main():
    # Cấu hình lại stdout hỗ trợ in ký tự tiếng Việt Unicode trên console Windows
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    
    query = "Những nghề người lao động chưa đủ 15 tuổi có thể làm"
    collection_name = "RAG_lawyer_1"
    search_k = 10
    rerank_k = 3

    print(f"--- Đang test SearchLawTool với query: '{query}' ---")
    print(f"search_k: {search_k}, rerank_k: {rerank_k}, collection: '{collection_name}'")

    try:
        # Chạy thử _run của SearchLawTool
        results = SearchLawTool._run(
            query=query,
            search_k=search_k,
            rerank_k=rerank_k,
            collection_name=collection_name
        )

        print(f"\nTìm thấy {len(results)} tài liệu kết quả:")
        for idx, doc in enumerate(results):
            score = doc.metadata.get("score", "N/A")
            print(f"\n[Tài liệu {idx + 1}] (Score: {score})")
            print(f"Metadata: {doc.metadata}")
            print(f"Nội dung: {doc.page_content[:200]}...")
            print("-" * 50)

    except Exception as e:
        print(f"Xảy ra lỗi trong quá trình test: {str(e)}")


if __name__ == "__main__":
    main()
