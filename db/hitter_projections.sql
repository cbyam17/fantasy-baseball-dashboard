-- fantasy_baseball_db.hitter_projections definition

CREATE TABLE `hitter_projections` (
  `ID` int NOT NULL,
  `NAME` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
  `TEAM` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
  `POS` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
  `R` double DEFAULT NULL,
  `HR` double DEFAULT NULL,
  `RBI` double DEFAULT NULL,
  `SB` double DEFAULT NULL,
  `H` double DEFAULT NULL,
  `SO` double DEFAULT NULL,
  `AVG` double DEFAULT NULL,
  `OPS` double DEFAULT NULL
  PRIMARY KEY (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;