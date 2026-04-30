-- fantasy_baseball_db.pitcher_zscore_view source

CREATE OR REPLACE
ALGORITHM = UNDEFINED VIEW `fantasy_baseball_db`.`pitcher_zscore_view` AS
select
    `base`.`ID` AS `ID`,
    `base`.`NAME` AS `NAME`,
    `base`.`TEAM` AS `TEAM`,
    `base`.`POS` AS `POS`,
    `base`.`QS` AS `QS`,
    `base`.`W` AS `W`,
    `base`.`L` AS `L`,
    `base`.`SV` AS `SV`,
    `base`.`HLD` AS `HLD`,
    `base`.`ERA` AS `ERA`,
    `base`.`WHIP` AS `WHIP`,
    `base`.`K` AS `K`,
    `base`.`ZSCORE_QS` AS `ZSCORE_QS`,
    `base`.`ZSCORE_W` AS `ZSCORE_W`,
    `base`.`ZSCORE_L` AS `ZSCORE_L`,
    `base`.`ZSCORE_SV` AS `ZSCORE_SV`,
    `base`.`ZSCORE_SVHLD` AS `ZSCORE_SVHLD`,
    `base`.`ZSCORE_ERA` AS `ZSCORE_ERA`,
    `base`.`ZSCORE_WHIP` AS `ZSCORE_WHIP`,
    `base`.`ZSCORE_K` AS `ZSCORE_K`,
    round(((((((`base`.`ZSCORE_W` + `base`.`ZSCORE_L`) + `base`.`ZSCORE_QS`) + `base`.`ZSCORE_ERA`) + `base`.`ZSCORE_WHIP`) + `base`.`ZSCORE_SVHLD`) + `base`.`ZSCORE_K`), 2) AS `ZSCORE_WMM`,
    round((((((`base`.`ZSCORE_W` + `base`.`ZSCORE_QS`) + `base`.`ZSCORE_ERA`) + `base`.`ZSCORE_WHIP`) + `base`.`ZSCORE_SV`) + `base`.`ZSCORE_K`), 2) AS `ZSCORE_LFL`
from
    (
    select
        `t`.`ID` AS `ID`,
        `t`.`NAME` AS `NAME`,
        `t`.`TEAM` AS `TEAM`,
        `t`.`POS` AS `POS`,
        `t`.`QS` AS `QS`,
        `t`.`W` AS `W`,
        `t`.`L` AS `L`,
        `t`.`SV` AS `SV`,
        `t`.`HLD` AS `HLD`,
        `t`.`ERA` AS `ERA`,
        `t`.`WHIP` AS `WHIP`,
        `t`.`K` AS `K`,
        round(((`t`.`QS` - avg(`t`.`QS`) OVER () ) / nullif(std(`t`.`QS`) OVER () , 0)), 2) AS `ZSCORE_QS`,
        round(((`t`.`W` - avg(`t`.`W`) OVER () ) / nullif(std(`t`.`W`) OVER () , 0)), 2) AS `ZSCORE_W`,
        round(((avg(`t`.`L`) OVER () - `t`.`L`) / nullif(std(`t`.`L`) OVER () , 0)), 2) AS `ZSCORE_L`,
        round(((`t`.`SV` - avg(`t`.`SV`) OVER () ) / nullif(std(`t`.`SV`) OVER () , 0)), 2) AS `ZSCORE_SV`,
        round((((`t`.`SV` + `t`.`HLD`) - avg((`t`.`SV` + `t`.`HLD`)) OVER () ) / nullif(std((`t`.`SV` + `t`.`HLD`)) OVER () , 0)), 2) AS `ZSCORE_SVHLD`,
        round(((avg(`t`.`ERA`) OVER () - `t`.`ERA`) / nullif(std(`t`.`ERA`) OVER () , 0)), 2) AS `ZSCORE_ERA`,
        round(((avg(`t`.`WHIP`) OVER () - `t`.`WHIP`) / nullif(std(`t`.`WHIP`) OVER () , 0)), 2) AS `ZSCORE_WHIP`,
        round(((`t`.`K` - avg(`t`.`K`) OVER () ) / nullif(std(`t`.`K`) OVER () , 0)), 2) AS `ZSCORE_K`
    from
        `fantasy_baseball_db`.`pitcher_projections` `t`) `base`;