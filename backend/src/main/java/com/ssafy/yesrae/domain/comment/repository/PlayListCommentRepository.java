package com.ssafy.yesrae.domain.comment.repository;

import com.ssafy.yesrae.domain.comment.entity.PlayListComment;
import org.springframework.data.jpa.repository.JpaRepository;

public interface PlayListCommentRepository extends JpaRepository<PlayListComment, Long> {

}
