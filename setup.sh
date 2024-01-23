

# Install required python packages
pip install -r requirements.txt

# Install spacy eng language model for sentence segmentation
python -m spacy download en_core_web_sm

# If postgresDB is not installed
# pgdb_setup.sh

# Setup the vector database for RAG
su -c 'psql < pgvector.sql' postgres 
