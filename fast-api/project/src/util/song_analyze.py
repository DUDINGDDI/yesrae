# 노맨틀 계획

"""
==================초기 계획==================
1. spotify 30 초 미리 듣기를 다운 받는다 (구현 O) 
2. 해당 데이터를 wav로 바꾸고 음원 분석 수행 후 지운다 (구현 O)
3. 음원 파일에서 음원 분석 기준(템포, mel_freq) 추출 (구현 O)
4. 음원 분석 데이터 DB에 저장 -> 유사도를 구하기 위한 데이터  (템포 컬럼, mel_freqs 컬럼 저장) (FAST API 사용)
5. 매일 일정한 시간이 되면 정답 곡 한개 선택 (인기도 고려) (1. cron 사용 2. 인기도 높은 곡에서 랜덤 선택 )
6. 템포, mel_freq 기준으로 두 곡간 유사도 구하는 메소드 (구현 O)
7. 정답곡을 기준으로 해당 곡과의 전체 곡의 유사도를 계산
8. DB 에 매일 정답곡 기준으로 유사도 데이터 [노래 id : 유사도] 저장 (유사도 높은 순 정렬) (redis 사용)
"""


"""
==================변경 사항==================
문제 : spotify 30초 미리 듣기 없는 경우가 존재 -> 음원 파일에서 템포, 멜로디 (mel_freq) 추출 불가
대안 : spotify API 에서 제공하는 음악에 대한 특징값 이용해서 가중치로 유사도 구하기 
        acousticness : 0 ~ 1 
        danceability : 0 ~ 1 
        energy : 0 ~ 1 
        instrumentalness :  0 ~ 1 
        key: -1 ~ 11
        liveness ~= 0 ~ 1 
        loudness = -60 ~ 0
        mode : 0 ~ 1
        speechiness : 0 ~ 1
        tempo : not defined
        time_signature : 3 ~ 7
        valence : 0 ~ 1

"""


"""
음원 박자, 멜로디 정보 분석 후 유사도 계산
"""

from scipy.spatial import distance
import librosa
import numpy as np
import wget
import os
import torchaudio
import torch


"""
# 박자 정보 추출
tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)

# 멜로디 정보 추출
melody, _ = librosa.core.piptrack(y=y1, sr=sr1)
mel_freqs1 = librosa.feature.melspectrogram(S=melody, sr=sr1)

melody2, _ = librosa.core.piptrack(y=y2, sr=sr2)
mel_freqs2 = librosa.feature.melspectrogram(S=melody2, sr=sr2)

# 멜로디 및 박자 정보 출력
print("Tempo (BPM):", tempo)
print("Beat Frames:", beat_frames)
print("Melody Frequencies (Hz):", mel_freqs)
tempo : BPM (분당 박자), beat_frames : 각 박자의 프레임 위치
melody_freqs :  각 시간 스텝에 해당하는 주파수,  각 시간 스텝에서 가장 높은 확률로 감지된 주파수
"""



"""
spotify 30초 미리 듣기 url로 음원 파일 가져오기
:url : 30초 음원 url
:return : 가져온 음원 파일 이름
"""
def getMusic(url):
    mp3_name = wget.download(url)
    return mp3_name

"""
음성 파일에서 오디오 시계열, 샘플링 주파수 정보 추출
:mp3_file : 음성 파일
:return : 오디오 시계열, 샘플링 주파수
"""
def loadmusic(mp3_file):
    # y : 오디오 신호를 나타내는 1차원 numpy 배열
    # sr : 샘플링 주파수(Sampling Rate), 연속적 신호에서 얻어진 초당 샘플링 횟수

    y, sr = librosa.load(mp3_file)
    print("duration ", len(y)/sr)
    return y, sr


"""
입력 받은 음성 정보에서 비트 정보 추출 
:y  : 오디오 시계열 데이터
:sr : 샘플링 주파수
:return : 예상 글로벌 템포 (분당 비트 수)
"""
def getTempo(y, sr):
    tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
    return tempo

"""
피치 추적, 멜 스펙토그램 정보 추출
:y  : 오디오 시계열 데이터
:sr : 샘플링 주파수, 속도
:return : 멜 스펙토그램 
"""
"""
# 입력 받은 노래의 멜로디 정보 추출
def getMelody(y, sr):

    # 간격 조절

    # 피치 정보
    melody, _ = librosa.core.piptrack(y=y, sr=sr)
    # S : 스펙토그램
    # mel_freqs = librosa.feature.melspectrogram(S=melody, sr=sr, n_mels=60)
    mel_freqs = librosa.feature.melspectrogram(S=melody, sr=sr)
    print("mel_freq_shape : ", mel_freqs.shape)
    print("type : ", type(mel_freqs[0][0]))

    # 평균
    mel_freqs_mean = np.mean(mel_freqs, axis=1)
    # 분산
    mel_freqs_var = np.var(mel_freqs, axis=1)
    print("mel_freq_mean_shape :", mel_freqs_mean.shape)
    print("mel_freqs_var_shape :", mel_freqs_var.shape)

    mel_mean_var_concat = np.concatenate((mel_freqs_mean, mel_freqs_var), axis = 0)
    print("mel_mean_var_concat : ",  mel_mean_var_concat.shape)
    return mel_mean_var_concat
"""

"""
피치 추적, 멜 스펙토그램 정보 추출
:y  : 오디오 시계열 데이터
:sr : 샘플링 주파수, 속도
:return : 멜 스펙토그램 
"""
# 입력 받은 노래의 멜로디 정보 추출
def getMelody(y, sr, today_song_file = None, method="mfcc"):

    # 간격 조절

    if method == "librosa_mfcc":
        feature = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13).transpose(0, 1)
    elif method == "kaldi_mfcc":
        y, sr = torchaudio.load(today_song_file)
        feature = torchaudio.compliance.kaldi.mfcc(y, num_ceps=40, num_mel_bins=40).numpy()
    
    else:
    # 피치 정보
        melody, _ = librosa.core.piptrack(y=y, sr=sr)
    # S : 스펙토그램
    # mel_freqs = librosa.feature.melspectrogram(S=melody, sr=sr, n_mels=60)
        feature = librosa.feature.melspectrogram(S=melody, sr=sr)
    
    print("mel_freq_shape : ", feature.shape)
    print("type : ", type(feature[0][0]))

    # 평균
    mel_freqs_mean = np.mean(feature, axis=1)
    # 분산
    mel_freqs_var = np.var(feature, axis=1)
    print("mel_freq_mean_shape :", mel_freqs_mean.shape)
    print("mel_freqs_var_shape :", mel_freqs_var.shape)

    mel_mean_var_concat = np.concatenate((mel_freqs_mean, mel_freqs_var), axis = 0)
    print("mel_mean_var_concat : ",  mel_mean_var_concat.shape)
    return  



"""
입력한 음원 파일명에 해당하는 파일 삭제
:filename : 파일명
"""
def deleteFile(filename):
    if os.path.isfile(filename):
        os.remove(filename)



"""
두 곡 유사도 계산 후 반환 (2차원 배열인 경우)
템포 차이 계산, 두 곡간의 mel_freqs 간의 코사인 유사성 계산 후 템포와 mel_freq 유사성 결합해 유사도 계산

:tempo1 : 노래 1의 예상 글로벌 템포
:tempo2 : 노래 2의 예상 글로벌 템포
:mel_freq1 : 노래 1의 멜 스펙토그램 
:mel_freq2 : 노래 2의 멜 스펙토그램 
:return : 계산한 두 곡간의 유사도 정보
"""
def calSimilarity_2D(tempo1, tempo2, mel_freq1, mel_freq2):

    # 두 곡간의 템포 차이 계산
    tempo_difference = abs(tempo1 - tempo2)

    # 산술 평균 계산
    mel_freq1_res = np.mean(mel_freq1, axis = -1)
    mel_freq2_res = np.mean(mel_freq2, axis = -1)

     # 두 곡의 mel_freqs 간의 코사인 유사성 계산
    cosine_sim = 1 - distance.cosine(mel_freq1_res.ravel(), mel_freq2_res.ravel())

    print(f"Tempo Difference: {tempo_difference}")
    print(f"Mel Frequency Cosine Similarity: {cosine_sim}")

    # 템포 와 mel_freqs 유사성을 결합하여 유사도 계산
    similarity_score = (20 * cosine_sim + (1 / (1 + tempo_difference))) / 21

    return similarity_score



"""
두 곡 유사도 계산 후 반환 (1차원 배열)
템포 차이 계산, 두 곡간의 mel_mean_var_concat 간의 코사인 유사성 계산 후 템포와 mel_mean_var_concat 유사성 결합해 유사도 계산

:tempo1 : 노래 1의 예상 글로벌 템포
:tempo2 : 노래 2의 예상 글로벌 템포
:mel_mean_var_concat1 : 노래 1의 평균, 분산 특성값 
:mel_mean_var_concat2 : 노래 2의 평균, 분산 특성값 
:return : 계산한 두 곡간의 유사도 정보
"""
def calSimilarity(tempo1, tempo2, mel_mean_var_concat1, mel_mean_var_concat2):

    # 두 곡간의 템포 차이 계산
    tempo_difference = abs(tempo1 - tempo2)

    # 두 곡의 mel_freqs 간의 코사인 유사성 계산
    cosine_sim = 1 - distance.cosine(mel_mean_var_concat1, mel_mean_var_concat2)

    print(f"Tempo Difference: {tempo_difference}")
    print(f"Mel Frequency Cosine Similarity: {cosine_sim}")

    # 템포 와 mel_freqs 유사성을 결합하여 유사도 계산
    similarity_score = (20 * cosine_sim + (1 / (1 + tempo_difference))) / 21

    return similarity_score


"""
test
"""

if __name__ == "__main__":

    try:
        # 음원 파일 저장하는 경로
        root_path = os.getcwd() +"\\"
        print(f"root path : {root_path}")

        # root_path = root_path + "\\src"
        # os.chdir(root_path)

        # 오늘의 노래
        today_song_url  = 'https://p.scdn.co/mp3-preview/8cd16a87465e35652134fb7cd4a276812690d750?cid=c551bf26249e4acf9eab170aed614fab'

        today_song_name = getMusic(today_song_url)
        today_song_file = root_path + today_song_name

        y1, sr1 = loadmusic(today_song_file)

        mel_mean_var_concat_1 = getMelody(y1, sr1)

        # 30초 미리 듣기 API 저장
        url = ['https://p.scdn.co/mp3-preview/a76a5bfcf5145901bd4b7ca88e248a2d897950d6?cid=c551bf26249e4acf9eab170aed614fab', 'https://p.scdn.co/mp3-preview/492d170729d672b0e224f399e116d5dafb80755f?cid=c551bf26249e4acf9eab170aed614fab'
            'https://p.scdn.co/mp3-preview/598e05a7fd20278aca5477e1993b252e8fc97daf?cid=c551bf26249e4acf9eab170aed614fab', 'https://p.scdn.co/mp3-preview/8dd93c0af476c8cce9a49b7ad7554c3bb1880555?cid=c551bf26249e4acf9eab170aed614fab',
            'https://p.scdn.co/mp3-preview/29bcbadcb6ee2d7ad5564c2ee5f17520afb1489b?cid=c551bf26249e4acf9eab170aed614fab', 'https://p.scdn.co/mp3-preview/7d0c01de9171bfde69ceeda7625f387f710dcc5b?cid=c551bf26249e4acf9eab170aed614fab']

        for idx, input_url in enumerate(url):

            # 음악 파일 load
            mp3_name = getMusic(input_url)
            
            mp3_file = root_path + mp3_name

            print("비교하는 노래 : {}".format(mp3_name))

            y2, sr2 = loadmusic(mp3_file)

            # 음원 파일에서 박자, 멜로디 추출
            mel_mean_var_concat_2 = getMelody(y2, sr2)

            # txt 파일 저장
            # output_file_1 = "mel_spectrogram_1.txt"
            # output_file_2 = "mel_spectrogram_2.txt"
            # with np.printoptions(threshold=np.inf):
            #     np.savetxt(output_file_1, mel_mean_var_concat_1)
            #     #print(mel_freqs_1)
            
            # with np.printoptions(threshold=np.inf):
            #     np.savetxt(output_file_2, mel_mean_var_concat_2)
            #     #print(mel_freqs_2)
            
            # 유사도 결과
            similarity_score = calSimilarity(getTempo(y1, sr1), getTempo(y2, sr2), mel_mean_var_concat_1, mel_mean_var_concat_2)
            print(f"Overall Similarity Score: {similarity_score}")

            deleteFile(mp3_name)
            deleteFile(today_song_name)
        
    except Exception as e:
        print("error :", e)
        deleteFile(mp3_name)
        deleteFile(today_song_name)
