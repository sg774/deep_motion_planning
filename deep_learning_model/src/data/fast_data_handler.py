
import os
import pandas as pd
import numpy as np

class FastDataHandler():
    """Class to load data from HDF5 storages in a random and chunckwise manner"""
    def __init__(self, filepath, batchsize = 16, chunksize=8192):
        self.filepath = filepath
        self.chunksize = chunksize
        self.batchsize = batchsize

        if not chunksize % batchsize == 0:
            raise IOError('chunksize must be divisible by batchsize')

        if not os.path.exists(filepath):
            raise IOError('File does not exists: {}'.format(filepath))

        # Get the number of rows without loading any data into memory
        with pd.HDFStore(filepath, mode='r') as store:
            self.nrows = store.get_storer('data').nrows

        # Make sure, we can return a chunk with the correct size
        if chunksize > self.nrows:
            raise ValueError('Chunksize is to large for the dataset: {} chunks > {} rows'.format(chunksize, self.nrows))

        self.batches = self.__generate_next_batch__()

    def steps_per_epoch(self):
        """
        Get the number of steps to process the entire dataset once
        """
        return self.nrows // self.batchsize

    def __generate_next_batch__(self):

        data_columns = None
        cmd_columns = None
        with pd.HDFStore(self.filepath, mode='r') as store:
            while True:
                current_index = 0
                for i in range(self.nrows // self.chunksize):
                    chunk = store.select('data',
                            start=i*self.chunksize, stop=(i+1)*self.chunksize)
                    chunk = chunk.reindex(np.random.permutation(chunk.index))

                    if not data_columns:
                        data_columns = list()
                        cmd_columns = list()
                        for j,column in enumerate(chunk.columns):
                            if column.split('_')[0] in ['laser','target']\
                                and not column.split('_')[1] == 'id':
                                data_columns.append(j)
                            if column in ['linear_x','angular_z']:
                                cmd_columns.append(j)

                    for j in range(chunk.shape[0] // self.batchsize):
                        yield (chunk.iloc[j*self.batchsize:(j+1)*self.batchsize, data_columns].values,
                        chunk.iloc[j*self.batchsize:(j+1)*self.batchsize, cmd_columns].values)
                        current_index += self.batchsize
            
    def next_batch(self):
        """
        Load the next random batch from the loaded data file

        @return (input data, ground truth commands)
        @rtype Tuple
        """
        # Load the data for the next batch
        return next(self.batches)

        