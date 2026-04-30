-- fantasy_baseball_db.pitcher_projections definition

CREATE TABLE `pitcher_projections` (
  `ID` int NOT NULL,
  `NAME` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
  `TEAM` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
  `POS` varchar(50) DEFAULT NULL,
  `QS` double DEFAULT NULL,
  `W` double DEFAULT NULL,
  `L` double DEFAULT NULL,
  `SV` int DEFAULT NULL,
  `HLD` int DEFAULT NULL,
  `ERA` double DEFAULT NULL,
  `WHIP` double DEFAULT NULL,
  `K` double DEFAULT NULL,
  PRIMARY KEY (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;