import chromadb
from sentence_transformers import SentenceTransformer
from chromadb.api.types import Documents, EmbeddingFunction, Embeddings
import json
from tqdm import tqdm

embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

def load_json(data_path):
    with open(data_path) as json_file:
        data = json.load(json_file)
    return data

class MyEmbeddingFunction(EmbeddingFunction):
    def __call__(self, input: Documents) -> Embeddings:
        batch_embeddings = embedding_model.encode(input)
        return batch_embeddings.tolist()
    
def load_basic_doc(src):
    with open(f'data/api_db/basic_rag_{src}.jsonl') as f:
        docs = [json.loads(x) for x in f.readlines()]
    return docs
    
def make_basic_rag_db(lib, docs):
    embed_fn = MyEmbeddingFunction()
    client = chromadb.PersistentClient(path='./docs_db')
    collection = client.get_or_create_collection(
        name=f'basic_rag_{lib}',
    )
    
    batch_size = 50

    for i in tqdm(range(0, len(docs), batch_size)):

        batch = docs[i : i + batch_size]


        batch_docs = [str(doc["document"]) if str(doc["document"]) != "" else "No document" for doc in batch]
        batch_ids = [str(j+i) for j in range(len(batch))]
        batch_metadata = [dict(title=doc["title"]) for doc in batch]

        batch_embeddings = embedding_model.encode(batch_docs)
        
        collection.upsert(
            ids=batch_ids,
            metadatas=batch_metadata,
            documents=batch_docs,
            embeddings=batch_embeddings.tolist(),
        )
        
def test_inference(lib):
    embed_fn = MyEmbeddingFunction()
    client = chromadb.PersistentClient(path='./docs_db')
    collection = client.get_or_create_collection(
        name=f'basic_rag_{lib}',
        embedding_function=embed_fn
    )

    retriever_results = collection.query(
        query_texts=["Generate unit test case for testing tf.shape() API"],
        n_results=3,
    )
    
    print(retriever_results["documents"])
    
def main():
    lib = 'tensorflow'
    docs = load_json('TensorFlow_train_data.json')
    make_basic_rag_db(lib, docs)
    test_inference(lib)
    
if __name__ == '__main__':
    main()