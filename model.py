import torch
import torch.nn as nn
import torchvision.models as models


class EncoderCNN(nn.Module):
    def __init__(self, embed_size):
        super(EncoderCNN, self).__init__()
        resnet = models.resnet50(pretrained=True)
        for param in resnet.parameters():
            param.requires_grad_(False)
        
        modules = list(resnet.children())[:-1]
        self.resnet = nn.Sequential(*modules)
        self.embed = nn.Linear(resnet.fc.in_features, embed_size)

    def forward(self, images):
        features = self.resnet(images)
        features = features.view(features.size(0), -1)
        features = self.embed(features)
        return features
    

class DecoderRNN(nn.Module):
    def __init__(self, embed_size, hidden_size, vocab_size, num_layers=1):
        super(DecoderRNN, self).__init__()

        self.hidden_size = hidden_size
        
        self.embed = nn.Embedding(vocab_size, embed_size)
        self.lstm = nn.LSTM(embed_size, hidden_size, num_layers, batch_first=True)
        self.linear = nn.Linear(hidden_size, vocab_size)
    
    def forward(self, features, captions):
        #print("features: {}, captions: {}".format(features.size(), captions.size()))
        cap_embedding = self.embed(captions[:, :-1])
        embeddings = torch.cat((features.unsqueeze(1), cap_embedding), 1)
        #print("embeddings: {}".format(embeddings.size()))
        
        lstm_out, hidden = self.lstm(embeddings)
        outputs = self.linear(lstm_out)
        #print("lstm_out: {}, hidden: {}, outputs: {}".format(lstm_out.size(), hidden[0].size(), outputs.size()))
        
        return outputs

    def sample(self, inputs, states=None, max_len=20):
        " accepts pre-processed image tensor (inputs) and returns predicted sentence (list of tensor ids of length max_len) "
        result = []
        for i in range(max_len):
            outputs, states = self.lstm(inputs, states)
            outputs = self.linear(outputs.squeeze(1))
            target_index = outputs.max(1)[1]
            result.append(target_index.item())
            inputs = self.embed(target_index).unsqueeze(1)
        return result
