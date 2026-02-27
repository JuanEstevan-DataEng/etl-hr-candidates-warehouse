SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0;
SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0;
SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION';

-- -----------------------------------------------------
-- Schema candidates_dw
-- -----------------------------------------------------

-- -----------------------------------------------------
-- Schema candidates_dw
-- -----------------------------------------------------
CREATE SCHEMA IF NOT EXISTS `candidates_dw` ;
USE `candidates_dw` ;

-- -----------------------------------------------------
-- Table `candidates_dw`.`dim_candidate`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `candidates_dw`.`dim_candidate` (
  `candidate_sk` INT NOT NULL AUTO_INCREMENT,
  `first_name` VARCHAR(100) NOT NULL,
  `last_name` VARCHAR(100) NOT NULL,
  `email` VARCHAR(50) NOT NULL,
  PRIMARY KEY (`candidate_sk`),
  UNIQUE INDEX `email_UNIQUE` (`email` ASC) VISIBLE)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `candidates_dw`.`dim_date`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `candidates_dw`.`dim_date` (
  `date_sk` INT NOT NULL,
  `full_date` DATE NOT NULL,
  `year` INT NOT NULL,
  `month` INT NOT NULL,
  `day` INT NOT NULL,
  `quarter` INT NOT NULL,
  PRIMARY KEY (`date_sk`))
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `candidates_dw`.`dim_location`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `candidates_dw`.`dim_location` (
  `location_sk` INT NOT NULL AUTO_INCREMENT,
  `country` VARCHAR(250) NOT NULL,
  PRIMARY KEY (`location_sk`))
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `candidates_dw`.`dim_technology`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `candidates_dw`.`dim_technology` (
  `technology_sk` INT NOT NULL AUTO_INCREMENT,
  `technology_name` VARCHAR(45) NOT NULL,
  PRIMARY KEY (`technology_sk`))
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `candidates_dw`.`dim_seniority`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `candidates_dw`.`dim_seniority` (
  `seniority_sk` INT NOT NULL AUTO_INCREMENT,
  `seniority_name` VARCHAR(45) NOT NULL,
  PRIMARY KEY (`seniority_sk`))
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `candidates_dw`.`fact_application`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `candidates_dw`.`fact_application` (
  `application_sk` INT NOT NULL AUTO_INCREMENT,
  `candidate_sk` INT NOT NULL,
  `seniority_sk` INT NOT NULL,
  `technology_sk` INT NOT NULL,
  `location_sk` INT NOT NULL,
  `date_sk` INT NOT NULL,
  `yoe` INT NOT NULL,
  `code_challenge_score` INT NOT NULL,
  `technical_interview_score` INT NOT NULL,
  `is_hired` TINYINT(1) NOT NULL,
  PRIMARY KEY (`application_sk`),
  INDEX `fk_fact_application_dim_candidate_idx` (`candidate_sk` ASC) VISIBLE,
  INDEX `fk_fact_application_dim_seniority1_idx` (`seniority_sk` ASC) VISIBLE,
  INDEX `fk_fact_application_dim_technology1_idx` (`technology_sk` ASC) VISIBLE,
  INDEX `fk_fact_application_dim_date1_idx` (`date_sk` ASC) VISIBLE,
  INDEX `fk_fact_application_dim_location1_idx` (`location_sk` ASC) VISIBLE,
  CONSTRAINT `fk_fact_application_dim_candidate`
    FOREIGN KEY (`candidate_sk`)
    REFERENCES `candidates_dw`.`dim_candidate` (`candidate_sk`),
  CONSTRAINT `fk_fact_application_dim_seniority1`
    FOREIGN KEY (`seniority_sk`)
    REFERENCES `candidates_dw`.`dim_seniority` (`seniority_sk`),
  CONSTRAINT `fk_fact_application_dim_technology1`
    FOREIGN KEY (`technology_sk`)
    REFERENCES `candidates_dw`.`dim_technology` (`technology_sk`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_fact_application_dim_date1`
    FOREIGN KEY (`date_sk`)
    REFERENCES `candidates_dw`.`dim_date` (`date_sk`),
  CONSTRAINT `fk_fact_application_dim_location1`
    FOREIGN KEY (`location_sk`)
    REFERENCES `candidates_dw`.`dim_location` (`location_sk`)
    )
ENGINE = InnoDB;


SET SQL_MODE=@OLD_SQL_MODE;
SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS;
SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS;
