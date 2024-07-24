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

def prepare_batch_data(data, mode):
    batch_docs = []
    for item in data:
        for change in item['changes']:
            if mode == 'patch_level':
                for patch in change['patches']:
                    batch_docs.append(patch['hunk'])
            else:
                batch_docs.append(change['whole_hunk'])

    return batch_docs

def make_basic_rag_db(lib, docs, mode='patch_level'):
    embed_fn = MyEmbeddingFunction()
    client = chromadb.PersistentClient(path='./docs_db')
    collection = client.get_or_create_collection(
        name=f"basic_rag_{mode}_{lib}",
    )
    
    batch_size = 50
    batch_docs = prepare_batch_data(docs, mode)
    for i in tqdm(range(0, len(batch_docs), batch_size)):
        
        batch = batch_docs[i : i + batch_size]
        batch_ids = [str(j+i) for j in range(len(batch))]
        # batch_ids = [str(item['Id']) for item in batch]
        # batch_metadata = [dict(label=doc["label"]) for doc in batch]
        
        batch_embeddings = embedding_model.encode(batch)
        
        collection.upsert(
            ids=batch_ids,
            # metadatas=batch_metadata,
            documents=batch,
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
        query_texts=["fix out of bound bug"],
        n_results=1,
    )
    print(retriever_results["documents"])
    
def main():
    lib = 'pytorch'
    mode = 'patch_level'
    docs = load_json('data/RAG_data/PyTorch_train_data.json')
    
    make_basic_rag_db(lib, docs, mode=mode)
    # test_inference(lib)
    
if __name__ == '__main__':
    main()