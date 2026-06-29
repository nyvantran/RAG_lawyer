import os
import glob
import json
import argparse
from dotenv import load_dotenv

# Load biến môi trường từ file .env ở thư mục gốc
load_dotenv()

try:
    from qdrant_client import QdrantClient
    from qdrant_client.http import models
except ImportError:
    raise ImportError(
        "Không thể import qdrant_client. Vui lòng cài đặt bằng lệnh: pip install qdrant-client"
    )

def main():
    parser = argparse.ArgumentParser(description="Chuẩn bị Vector Store Qdrant và upsert dữ liệu luật lao động.")
    parser.add_argument(
        "--qdrant-url", 
        type=str, 
        default=os.getenv("QDRANT_URL", "http://localhost:6333"), 
        help="URL kết nối tới Qdrant (mặc định lấy từ QDRANT_URL trong .env hoặc http://localhost:6333)"
    )
    parser.add_argument(
        "--collection", 
        type=str, 
        default="RAG_lawyer", 
        help="Tên collection cần tạo và upsert dữ liệu (mặc định: RAG_lawyer)"
    )
    parser.add_argument(
        "--data-dir", 
        type=str, 
        default="data/LuatLaoDong2025_temp", 
        help="Thư mục chứa các file JSON dữ liệu luật (mặc định: data/LuatLaoDong2025_temp)"
    )
    parser.add_argument(
        "--recreate", 
        action="store_true", 
        help="Xóa và tạo mới lại collection nếu đã tồn tại"
    )
    parser.add_argument(
        "--batch-size", 
        type=int, 
        default=50, 
        help="Kích thước batch khi upsert điểm vào Qdrant (mặc định: 50)"
    )
    
    args = parser.parse_args()
    
    print(f"🔌 Đang kết nối tới Qdrant tại: {args.qdrant_url}")
    client = QdrantClient(url=args.qdrant_url)
    
    # Quét danh sách file JSON dữ liệu
    search_pattern = os.path.join(args.data_dir, "*.json")
    json_files = glob.glob(search_pattern)
    if not json_files:
        print(f"❌ Không tìm thấy file JSON nào trong thư mục: {args.data_dir}")
        return
        
    print(f"📂 Tìm thấy {len(json_files)} file tài liệu JSON để xử lý.")
    
    # Kiểm tra sự tồn tại của collection
    try:
        collections = client.get_collections().collections
        collection_names = [col.name for col in collections]
        exists = args.collection in collection_names
    except Exception as e:
        print(f"❌ Lỗi kết nối tới Qdrant: {e}")
        print("Vui lòng đảm bảo Qdrant container đang chạy (chạy 'make up' hoặc 'docker compose up -d').")
        return

    # Tái tạo collection nếu được yêu cầu
    if exists and args.recreate:
        print(f"🗑️ Đang xóa collection cũ '{args.collection}'...")
        client.delete_collection(args.collection)
        exists = False
        
    # Tạo mới collection với 3 trường vector
    if not exists:
        print(f"🆕 Đang tạo collection mới '{args.collection}'...")
        client.create_collection(
            collection_name=args.collection,
            vectors_config={
                "metadata_embedded": models.VectorParams(size=1024, distance=models.Distance.COSINE),
                "page_content_embedded": models.VectorParams(size=1024, distance=models.Distance.COSINE),
                "fuse_embedded": models.VectorParams(size=1024, distance=models.Distance.COSINE)
            }
        )
        print(f"✅ Đã tạo thành công collection '{args.collection}'.")
    else:
        print(f"📝 Collection '{args.collection}' đã tồn tại. Dữ liệu mới sẽ được upsert đè/bổ sung.")
        
    # Đọc và chuyển đổi dữ liệu từ các file JSON
    print("⏳ Đang tải và phân tích các tài liệu...")
    points = []
    for filepath in json_files:
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                
                # Trích xuất 3 trường vector tương ứng
                vectors = {
                    "metadata_embedded": data["vector"]["metadata_embedded"],
                    "page_content_embedded": data["vector"]["page_content_embedded"],
                    "fuse_embedded": data["vector"]["fuse_embedded"]
                }
                
                points.append(
                    models.PointStruct(
                        id=data["id"],
                        payload=data["payload"],
                        vector=vectors
                    )
                )
        except Exception as e:
            print(f"⚠️ Lỗi xử lý file {os.path.basename(filepath)}: {e}")
            
    print(f"✅ Đã tải xong {len(points)} điểm dữ liệu.")
    
    # Tiến hành upsert theo từng batch
    print(f"🚀 Bắt đầu upsert dữ liệu vào Qdrant (batch size = {args.batch_size})...")
    success_count = 0
    for i in range(0, len(points), args.batch_size):
        batch = points[i:i + args.batch_size]
        try:
            client.upsert(
                collection_name=args.collection,
                points=batch
            )
            success_count += len(batch)
            print(f"  🔹 Đã đẩy thành công {success_count}/{len(points)} tài liệu...")
        except Exception as e:
            print(f"❌ Lỗi upsert batch từ chỉ mục {i}: {e}")
            
    print(f"🎉 Hoàn thành! Đã chuẩn bị xong vector store và import thành công {success_count} tài liệu vào Qdrant.")

if __name__ == "__main__":
    main()
