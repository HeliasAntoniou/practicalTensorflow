import tensorflow as tf

from rnn.stacked_rnn.model import RNNModel
from rnn.stacked_rnn.helias_cell import HeliasCell


class DynamicHeliasCell(RNNModel):

    def __init__(self, num_steps):
        super(DynamicHeliasCell, self).__init__(num_steps)

    def _build_graph(self,
                     state_size=100,
                     num_layers=3):
        tf.reset_default_graph()

        x = tf.placeholder(tf.int32, [self.BATCH_SIZE, self.NUM_STEPS], name='input_placeholder')
        y = tf.placeholder(tf.int32, [self.BATCH_SIZE, self.NUM_STEPS], name='labels_placeholder')

        print("")
        print("Input placeholder : {}".format(x.shape))
        print("Output placeholder: {}".format(y.shape))
        print("")

        embeddings = tf.get_variable('embedding_matrix', [self.NUM_CLASSES, state_size])

        # Note that our inputs are no longer a list, but a tensor of dims batch_size x num_steps x state_size
        rnn_inputs = tf.nn.embedding_lookup(embeddings, x)

        print("Dynamic RNN input : {}".format(rnn_inputs.shape))
        print("")

        cells = []
        for i in range(num_layers):
            with tf.variable_scope("LSTM_{}".format(i)):
                cell = HeliasCell(state_size, 5)
                cells.append(cell)

        cell = tf.nn.rnn_cell.MultiRNNCell(cells)

        init_state = cell.zero_state(self.BATCH_SIZE, tf.float32)
        rnn_outputs, final_state = tf.nn.dynamic_rnn(cell, rnn_inputs, initial_state=init_state)

        with tf.variable_scope('softmax'):
            W = tf.get_variable('W', [state_size, self.NUM_CLASSES])
            b = tf.get_variable('b', [self.NUM_CLASSES], initializer=tf.constant_initializer(0.0))

        # reshape rnn_outputs and y so we can get the logits in a single matmul
        rnn_outputs = tf.reshape(rnn_outputs, [-1, state_size])
        y_reshaped = tf.reshape(y, [-1])

        logits = tf.matmul(rnn_outputs, W) + b

        predictions = tf.nn.softmax(logits)

        total_loss = tf.reduce_mean(tf.nn.sparse_softmax_cross_entropy_with_logits(logits=logits, labels=y_reshaped))
        train_step = tf.train.AdamOptimizer(self.LEARNING_RATE).minimize(total_loss)

        return dict(
            x=x,
            y=y,
            init_state=init_state,
            predictions=predictions,
            final_state=final_state,
            total_loss=total_loss,
            train_step=train_step
        )


rnn = DynamicHeliasCell(5)
graph = rnn.build_graph()
rnn.train_network(graph, 10, save="./checkpoints/helias-dynamic")
rnn.generate_characters(graph, "./checkpoints/helias-dynamic", 1000, prompt='HELIAS', pick_top_chars=2)
