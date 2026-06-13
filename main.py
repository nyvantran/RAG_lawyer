from app.core.tool import VectorSearchTool



query = "Phụ lục V - Danh mục nghề, công việc người từ đủ 15 tuổi đến chưa đủ 18 tuổi"

docs = VectorSearchTool._run(
    query=query,
    k=5,
    collection_name="RAG_lawer"
)

for doc in docs:
    print(f"score: {doc[1]}", end="\n" + "-" * 80 + "\n")
    print(doc[0].page_content, end="\n" + "-" * 80 + "\n")
    print(doc[0].metadata, end="\n" + "-" * 80 + "\n")
