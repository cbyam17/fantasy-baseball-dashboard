-- fantasy_baseball_db.hitter_zscore_view source

CREATE OR REPLACE
ALGORITHM = UNDEFINED VIEW `fantasy_baseball_db`.`hitter_zscore_view` AS
select
    `base`.`ID` AS `ID`,
    `base`.`NAME` AS `NAME`,
    `base`.`TEAM` AS `TEAM`,
    `base`.`R` AS `R`,
    `base`.`HR` AS `HR`,
    `base`.`RBI` AS `RBI`,
    `base`.`SB` AS `SB`,
    `base`.`H` AS `H`,
    `base`.`K` AS `K`,
    `base`.`AVG` AS `AVG`,
    `base`.`OPS` AS `OPS`,
    `base`.`POS` AS `POS`,
    `base`.`ZSCORE_R` AS `ZSCORE_R`,
    `base`.`ZSCORE_HR` AS `ZSCORE_HR`,
    `base`.`ZSCORE_RBI` AS `ZSCORE_RBI`,
    `base`.`ZSCORE_SB` AS `ZSCORE_SB`,
    `base`.`ZSCORE_H` AS `ZSCORE_H`,
    `base`.`ZSCORE_K` AS `ZSCORE_K`,
    `base`.`ZSCORE_AVG` AS `ZSCORE_AVG`,
    `base`.`ZSCORE_OPS` AS `ZSCORE_OPS`,
    round(((((((`base`.`ZSCORE_R` + `base`.`ZSCORE_HR`) + `base`.`ZSCORE_RBI`) + `base`.`ZSCORE_SB`) + `base`.`ZSCORE_H`) + `base`.`ZSCORE_K`) + `base`.`ZSCORE_OPS`), 1) AS `ZSCORE_WMM`,
    round((((((`base`.`ZSCORE_R` + `base`.`ZSCORE_HR`) + `base`.`ZSCORE_RBI`) + `base`.`ZSCORE_SB`) + `base`.`ZSCORE_AVG`) + `base`.`ZSCORE_OPS`), 1) AS `ZSCORE_LFL`
from
    (
    select
        `t`.`ID` AS `ID`,
        `t`.`NAME` AS `NAME`,
        `t`.`TEAM` AS `TEAM`,
        `t`.`R` AS `R`,
        `t`.`HR` AS `HR`,
        `t`.`RBI` AS `RBI`,
        `t`.`SB` AS `SB`,
        `t`.`H` AS `H`,
        `t`.`K` AS `K`,
        `t`.`AVG` AS `AVG`,
        `t`.`OPS` AS `OPS`,
        `t`.`POS` AS `POS`,
        round(((`t`.`R` - avg(`t`.`R`) OVER () ) / nullif(std(`t`.`R`) OVER () , 0)), 1) AS `ZSCORE_R`,
        round(((`t`.`HR` - avg(`t`.`HR`) OVER () ) / nullif(std(`t`.`HR`) OVER () , 0)), 1) AS `ZSCORE_HR`,
        round(((`t`.`RBI` - avg(`t`.`RBI`) OVER () ) / nullif(std(`t`.`RBI`) OVER () , 0)), 1) AS `ZSCORE_RBI`,
        round(((`t`.`SB` - avg(`t`.`SB`) OVER () ) / nullif(std(`t`.`SB`) OVER () , 0)), 1) AS `ZSCORE_SB`,
        round(((`t`.`H` - avg(`t`.`H`) OVER () ) / nullif(std(`t`.`H`) OVER () , 0)), 1) AS `ZSCORE_H`,
        round(((avg(`t`.`K`) OVER () - `t`.`K`) / nullif(std(`t`.`K`) OVER () , 0)), 1) AS `ZSCORE_K`,
        round(((`t`.`AVG` - avg(`t`.`AVG`) OVER () ) / nullif(std(`t`.`AVG`) OVER () , 0)), 1) AS `ZSCORE_AVG`,
        round(((`t`.`OPS` - avg(`t`.`OPS`) OVER () ) / nullif(std(`t`.`OPS`) OVER () , 0)), 1) AS `ZSCORE_OPS`
    from
        `fantasy_baseball_db`.`hitter_projections` `t`) `base`;