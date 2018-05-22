// Fill out your copyright notice in the Description page of Project Settings.

#pragma once

#include "Settings/SensorDescription.h"

#include "LidarDescription.generated.h"

UCLASS()
class CARLA_API ULidarDescription : public USensorDescription
{
  GENERATED_BODY()

public:

  virtual void AcceptVisitor(ISensorDescriptionVisitor &Visitor) const final
  {
    Visitor.Visit(*this);
  }

  virtual void Load(const FIniFile &Config, const FString &Section) final;

  virtual void Validate() final;

  virtual void Log() const final;

  /** Number of lasers. */
  UPROPERTY(EditDefaultsOnly, Category = "Lidar Description")
  uint32 Channels = 32u;

  /** Measure distance in centimeters. */
  UPROPERTY(EditDefaultsOnly, Category = "Lidar Description")
  float Range = 5000.0f;

  /** Points generated by all lasers per second. */
  UPROPERTY(EditDefaultsOnly, Category = "Lidar Description")
  uint32 PointsPerSecond = 56000u;

  /** Lidar rotation frequency. */
  UPROPERTY(EditDefaultsOnly, Category = "Lidar Description")
  float RotationFrequency = 10.0f;

  /**
   * Upper laser angle, counts from horizontal, positive values means above
   * horizontal line.
   */
  UPROPERTY(EditDefaultsOnly, Category = "Lidar Description")
  float UpperFovLimit = 10.0f;

  /**
   * Lower laser angle, counts from horizontal, negative values means under
   * horizontal line.
   */
  UPROPERTY(EditDefaultsOnly, Category = "Lidar Description")
  float LowerFovLimit = -30.0f;

  /** Wether to show debug points of laser hits in simulator. */
  UPROPERTY(EditDefaultsOnly, Category = "Lidar Description")
  bool ShowDebugPoints = false;

  /** The numercal value noise of lidar points. */
  UPROPERTY(EditDefaultsOnly, Category = "Lidar Description")
  float GaussianNoise = 0.0f;
  //claude

  /** The pattern of lidar points' dropout . */
  UPROPERTY(EditDefaultsOnly, Category = "Lidar Description")
  float DropOutPattern = 1.0f;
  //claude

  /** The pattern of lidar type . */
  UPROPERTY(EditDefaultsOnly, Category = "Lidar Description")
  uint32 LidarType = 1u;
  //claude

  /** The flag to debug . */
  UPROPERTY(EditDefaultsOnly, Category = "Lidar Description")
  uint32 DebugFlag = 2016u;
  //claude

  /** The pattern of lidar points' dropout . */
  UPROPERTY(EditDefaultsOnly, Category = "Lidar Description")
  float HorizonRange = 360.0f;
  //claude

};
