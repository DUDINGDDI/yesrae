package com.ssafy.yesrae.domain.tournament.service;

import com.ssafy.yesrae.common.exception.NoDataException;
import com.ssafy.yesrae.domain.tournament.dto.request.FindTournamentSongGetReq;
import com.ssafy.yesrae.domain.tournament.dto.request.RegistTournamentResultPostReq;
import com.ssafy.yesrae.domain.tournament.dto.response.TournamentSongFindRes;
import com.ssafy.yesrae.domain.tournament.entity.Tournament;
import com.ssafy.yesrae.domain.tournament.entity.TournamentResult;
import com.ssafy.yesrae.domain.tournament.entity.TournamentSong;
import com.ssafy.yesrae.domain.tournament.repository.TournamentRepository;
import com.ssafy.yesrae.domain.tournament.repository.TournamentResultRepository;
import com.ssafy.yesrae.domain.tournament.repository.TournamentSongRepository;
import com.ssafy.yesrae.domain.user.entity.User;
import com.ssafy.yesrae.domain.user.repository.UserRepository;
import java.util.List;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/**
 * 이상형 월드컵을 위한 API 서비스
 */
@Slf4j
@Transactional
@Service
public class TournamentServiceImpl implements TournamentService{

    private final TournamentSongRepository tournamentSongRepository;
    private final UserRepository userRepository;
    private final TournamentRepository tournamentRepository;
    private final TournamentResultRepository tournamentResultRepository;

    @Autowired
    public TournamentServiceImpl(TournamentSongRepository tournamentSongRepository,
        UserRepository userRepository, TournamentRepository tournamentRepository,
        TournamentResultRepository tournamentResultRepository) {
        this.tournamentSongRepository = tournamentSongRepository;
        this.userRepository = userRepository;
        this.tournamentRepository = tournamentRepository;
        this.tournamentResultRepository = tournamentResultRepository;
    }

    /**
     * 이상형 월드컵을 시작하기 위해 필요한 노래를 가져옴
     * @param findTournamentSongGetReq : 라운드 수
     */
    @Override
    public List<TournamentSongFindRes> findTournamentSong(
        FindTournamentSongGetReq findTournamentSongGetReq) {

        log.info("TournamentService_findTournamentSong_start: "
            + findTournamentSongGetReq.toString());

        List<TournamentSongFindRes> findRes = tournamentSongRepository.findTournamentSong(findTournamentSongGetReq);

        log.info("TournamentService_findTournamentSong_end: success");
        return findRes;
    }

    /**
     * 플레이 한 이상형 월드컵을 각 플레이 시점 마다 구분할 수 있도록 DB에 저장
     * @param userId : 이상형 월드컵 생성한 유저 ID
     */
    @Override
    public void registTournament(Long userId) {

        log.info("TournamentService_registTournament_start: "
            + userId);

        User user = userRepository.findById(userId)
            .orElseThrow(NoDataException::new);
        Tournament tournament = Tournament.builder()
            .user(user)
            .build();

        tournamentRepository.save(tournament);

        log.info("TournamentService_registTournament_end: success");
    }

    /**
     * 이상형 월드컵 결과를 DB에 저장하는 API
     * @param registTournamentResultPostReq : 이상형 월드컵 진행 결과 1등 ~ 4등
     */
    @Override
    public void registTournamentResult(
        RegistTournamentResultPostReq registTournamentResultPostReq) {

        log.info("TournamentService_registTournamentResult_start: "
            + registTournamentResultPostReq.toString());

        Tournament tournament = tournamentRepository.findById(registTournamentResultPostReq.getTournamentId())
            .orElseThrow(NoDataException::new);

        TournamentSong songOne = tournamentSongRepository.findById(registTournamentResultPostReq.getFirstSongId())
            .orElseThrow(NoDataException::new);
        TournamentSong songTwo = tournamentSongRepository.findById(registTournamentResultPostReq.getSecondSongId())
            .orElseThrow(NoDataException::new);
        TournamentSong songThree = tournamentSongRepository.findById(registTournamentResultPostReq.getSemiFinalSongOneId())
            .orElseThrow(NoDataException::new);
        TournamentSong songFour = tournamentSongRepository.findById(registTournamentResultPostReq.getSemiFinalSongTwoId())
            .orElseThrow(NoDataException::new);

        TournamentResult tournamentResultOne = TournamentResult.builder()
            .tournament(tournament)
            .tournamentSong(songOne)
            .rank(1)
            .build();
        TournamentResult tournamentResultTwo = TournamentResult.builder()
            .tournament(tournament)
            .tournamentSong(songTwo)
            .rank(2)
            .build();
        TournamentResult tournamentResultThree = TournamentResult.builder()
            .tournament(tournament)
            .tournamentSong(songThree)
            .rank(3)
            .build();
        TournamentResult tournamentResultFour = TournamentResult.builder()
            .tournament(tournament)
            .tournamentSong(songFour)
            .rank(3)
            .build();

        tournamentResultRepository.save(tournamentResultOne);
        tournamentResultRepository.save(tournamentResultTwo);
        tournamentResultRepository.save(tournamentResultThree);
        tournamentResultRepository.save(tournamentResultFour);

        log.info("TournamentService_registTournamentResult_end: success");
    }
}
