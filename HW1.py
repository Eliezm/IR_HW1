import os
import re

# Part 1: InvertedIndex
class InvertedIndex:
    def __init__(self, collection_path):
        """
        Initialize the inverted index from the AP collection.
        Using internal IDs instead of the original IDs to optimize query processing, 
        and saving the real ones linked to the internal ones in docs_ids.
        Saving the posting lists of each term in a sorted way in words_dict.

        :param collection_path: path to the AP collection
        """

        # Initialize relevant dictionaries
        self.docs_ids = {}  # internal id and original id translation dictionary, where the internal is the key
        self.words_dict = {}  # dictionary for storing the index,
                              # where the term is the key and the posting list is the value
        self.internal_id = 1

        # Patterns for breaking down a document into terms
        doc_pattern = re.compile(r"<DOC>(.*?)</DOC>", re.DOTALL)
        docno_pattern = re.compile(r"<DOCNO>\s*(.*?)\s*</DOCNO>")
        text_pattern = re.compile(r"<TEXT>(.*?)</TEXT>", re.DOTALL)

        # Breaking down all the files in the collection to documents
        # and saving their IDs from <DOCNO> part in the document
        # and update the terms posting list from the <TEXT> part
        for file_name in os.listdir(collection_path):
            file_path = os.path.join(collection_path, file_name)
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            docs = doc_pattern.findall(content)

            for doc in docs:
                # Retrieve document ID from its document in the file
                id = docno_pattern.search(doc).group(1)
                # Assign to this document his internal id in the index
                self.docs_ids[self.internal_id] = id

                # Term splitting within a document and updating its posting list in the index (words_dict)
                text_blocks = text_pattern.findall(doc)
                text = " ".join(text_blocks)
                words = set(text.split())
                for word in words:
                    if word not in self.words_dict:
                        self.words_dict[word] = [self.internal_id]
                    else:
                        self.words_dict[word].append(self.internal_id)

                # The internal ID raised by one for the next document internal ID
                self.internal_id += 1

    def get_number_of_documents(self) -> int:
        """
        Get the number of documents recorded in the index.
        """
        return self.internal_id - 1  # Minus 1 because the internal_id counter is always advancing by 1.

    def get_real_doc_id(self, internal_id: int) -> int:
        """
        Get the real ID from the internal ID of a document
        """
        return self.docs_ids[internal_id]

    def get_posting_list(self, term: str) -> list:
        """
        Get the posting list for a given term from the index.
        If the term is not in the index, return an empty list.
        :param term: a word
        :return: list of document ids in which the term appears
        """
        return self.words_dict.get(term, [])


# Part 2: Boolean Retrieval Model
class BooleanRetrieval:
    def __init__(self, inverted_index):
        """
        Initialize the boolean retrieval model.
        """
        self.inverted_index = inverted_index

    def run_query(self, query: str) -> list:
        """
        Run the given query on the index. Performing operations on posting lists.
        Algorithm inspired by the second code in the LeetCode link that was given in the HW.
        :param query: a boolean query in Reverse Polish Notation format
        :return: list of document ids
        """
        print("Original query:", query)

        # All text is in lowercase, so the query needs to be the same
        query = query.lower().split()

        # If the query is 1 word, we only need its posting list and to convert it to original doc ids
        if len(query) == 1:
            return self.change_to_docs_ids(self.inverted_index.get_posting_list(query[0]))

        stack = []

        # For printing the query in regular format after changing from Reverse Polish Notation format
        # africa airlines NOT should give (NOT airlines) AND africa
        expr_stack = []

        OPERATORS = ['and', 'or', 'not']

        # For each token in the query, we want to apply 'or', 'and', or 'not' on the term's posting list
        for token in query:
            if token not in OPERATORS:
                # For a term, we save its posting list to the stack
                stack.append(self.inverted_index.get_posting_list(token))
                expr_stack.append(token)
            else:
                if token == 'and':
                    a = stack.pop()
                    b = stack.pop()
                    stack.append(self.AND_func(a, b))
                    b_expr = expr_stack.pop()
                    a_expr = expr_stack.pop()
                    expr_stack.append(f"({a_expr} AND {b_expr})")

                if token == 'or':
                    a = stack.pop()
                    b = stack.pop()
                    stack.append(self.OR_func(a, b))
                    b_expr = expr_stack.pop()
                    a_expr = expr_stack.pop()
                    expr_stack.append(f"({a_expr} OR {b_expr})")

                if token == 'not':
                    a = stack.pop()
                    stack.append(self.NOT_func(a))
                    a_expr = expr_stack.pop()
                    expr_stack.append(f"(NOT {a_expr})")

        # In Reverse Polish Notation, sometimes 'AND' isn't noted,
        # so we need to check if there are 2 remaining posting lists in the stack and apply 'AND' to them
        if len(stack) == 2:
            a = stack.pop()
            b = stack.pop()
            internal_id_docs = self.AND_func(a, b)
            a_expr = expr_stack.pop()
            b_expr = expr_stack.pop()
            expr_stack.append(f"({b_expr} AND {a_expr})")

        else:
            internal_id_docs = stack.pop()

        print("Final executed query:", expr_stack[-1])

        # Because we work with internal ids, we need to convert them to their real ids
        return self.change_to_docs_ids(internal_id_docs)

    def change_to_docs_ids(self, internal_id_docs: list) -> list:
        """
        Change from internal IDs to real documents IDs
        :param internal_id_docs: list of internal documents IDs
        :return: real documents IDs
        """
        docs_ids = []
        for id in internal_id_docs:
            docs_ids.append(self.inverted_index.get_real_doc_id(id))

        return docs_ids

    @staticmethod
    def AND_func(left_postings: list, right_postings: list) -> list:
        """
        Find the documents that are in both posting list
        :param a: list
        :param b: list
        :return: intersection documents of two posting list
        """
        and_docs = []
        i, j = 0, 0
        while i < len(left_postings) and j < len(right_postings):
            if left_postings[i] == right_postings[j]:
                and_docs.append(left_postings[i])
                i += 1
                j += 1
            elif left_postings[i] < right_postings[j]:
                i += 1
            else:
                j += 1
        return and_docs

    @staticmethod
    def OR_func(left_postings: list, right_postings: list) -> list:
        """
        Combine two posting list
        :param a: list
        :param b: list
        :return: combination of two posting lists
        """
        union_docs = []
        i, j = 0, 0
        while i < len(left_postings) and j < len(right_postings):
            if left_postings[i] < right_postings[j]:
                union_docs.append(left_postings[i])
                i += 1
            elif left_postings[i] > right_postings[j]:
                union_docs.append(right_postings[j])
                j += 1
            else:
                union_docs.append(left_postings[i])
                i += 1
                j += 1

        if i == len(left_postings) and j != len(right_postings):
            while j < len(b):
                union_docs.append(right_postings[j])
                j += 1

        if j == len(b) and i != len(a):
            while i < len(a):
                union_docs.append(left_postings[i])
                i += 1

        return union_docs

    def NOT_func(self, posting_list: list) -> list:
        """
        Find the complement of the posting list
        :param a: list
        :return: complementary of posting list
        """
        not_docs = []
        num_docs = self.inverted_index.get_number_of_documents()
        # All documents internal ids in one posting list
        all_docs = [i for i in range(1, num_docs + 1)]

        i, j = 0, 0

        while i < len(posting_list):
            if all_docs[j] != posting_list[i]:
                not_docs.append(all_docs[j])
                j += 1
            else:
                i += 1
                j += 1

        while j < num_docs:
            not_docs.append(all_docs[j])
            j += 1

        return not_docs


if __name__ == "__main__":
    # We didn't succeed in connecting the VM to PyCharm,
    # so we downloaded the files to our computer from the VM and worked from there
    path_to_AP_collection = 'AP_Coll_Parsed'
    path_to_boolean_queries = 'BooleanQueries.txt'

    # Part 1
    inverted_index = InvertedIndex(path_to_AP_collection)

    # Part 2
    boolean_retrieval = BooleanRetrieval(inverted_index=inverted_index)

    # Read queries from file
    with open(path_to_boolean_queries, 'r') as f:
        queries = f.readlines()

    # Run queries and write results to file
    with open("Part_2.txt", 'w') as f:
        for query in queries:
            result = boolean_retrieval.run_query(query)
            f.write(' '.join(result) + '\n')

    # Part 3
    # Sort the terms in descending order to find the 10 most frequent words in the index
    ten_freq_words = sorted(inverted_index.words_dict.items(), key=lambda item: (-len(item[1]), item[0]))[:10]
    # Sort the terms in ascending order to find the 10 least frequent words in the index
    ten_less_freq_words = sorted(inverted_index.words_dict.items(), key=lambda item: (len(item[1]), item[0]))[:10]

    # Write the 10 most frequent words to a file with their document count
    with open("Part_3a.txt", "w") as f:
        for word, docs_list in ten_freq_words:
            f.write(f"{word}: {len(docs_list)} \n")

    # Write the 10 least frequent words to a file with their document count
    with open("Part_3b.txt", "w") as f:
        for word, docs_list in ten_less_freq_words:
            f.write(f"{word}: {len(docs_list)} \n")


