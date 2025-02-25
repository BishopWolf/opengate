/* --------------------------------------------------
Copyright (C): OpenGATE Collaboration
   This software is distributed under the terms
   of the GNU Lesser General  Public Licence (LGPL)
   See LICENSE.md for further details
   -------------------------------------------------- */

#include "GateComptonSplittingFreeFlightOptn.h"
#include "../GateHelpers.h"
#include "G4BiasingProcessInterface.hh"
#include "G4EmParameters.hh"
#include "G4GammaGeneralProcess.hh"
#include "G4ParticleChangeForGamma.hh"
#include "G4RunManager.hh"

GateComptonSplittingFreeFlightOptn::GateComptonSplittingFreeFlightOptn(
    const G4String &name)
    : G4VBiasingOperation(name), fSplittingFactor(1) {
  fAAManager = nullptr;
}

const G4VBiasingInteractionLaw *
GateComptonSplittingFreeFlightOptn::ProvideOccurenceBiasingInteractionLaw(
    const G4BiasingProcessInterface *, G4ForceCondition &) {
  return nullptr;
}

G4double GateComptonSplittingFreeFlightOptn::DistanceToApplyOperation(
    const G4Track *, G4double, G4ForceCondition *) {
  return DBL_MAX;
}

G4VParticleChange *
GateComptonSplittingFreeFlightOptn::GenerateBiasingFinalState(const G4Track *,
                                                              const G4Step *) {
  return nullptr;
}

void GateComptonSplittingFreeFlightOptn::SetSplittingFactor(
    const G4int splittingFactor) {
  fSplittingFactor = splittingFactor;
}

void GateComptonSplittingFreeFlightOptn::InitializeAAManager(
    const py::dict &user_info) {
  fAAManager = new GateAcceptanceAngleTesterManager();
  fAAManager->Initialize(user_info, true);

  if (G4EmParameters::Instance()->GeneralProcessActive() == false) {
    Fatal("GeneralGammaProcess is not active. This is needed for "
          "ComptonSplittingFreeFlight");
  }
}

G4VParticleChange *GateComptonSplittingFreeFlightOptn::ApplyFinalStateBiasing(
    const G4BiasingProcessInterface *callingProcess, const G4Track *track,
    const G4Step *step, G4bool &) {
  // DDD("ApplyFinalStateBiasing");
  // DDD(track->GetWeight());
  const double weight = track->GetWeight() / fSplittingFactor;
  const auto position = step->GetPostStepPoint()->GetPosition();
  // DDD(position);

  // debug
  const auto *wrapped_p = callingProcess->GetWrappedProcess();
  const auto *ggp = static_cast<const G4GammaGeneralProcess *>(wrapped_p);
  const auto *proc = ggp->GetSelectedProcess();
  if (proc != nullptr) {
    // DDD(proc->GetProcessName());
  }

  // This is the initial scattered Gamma
  auto *processFinalStateForGamma =
      callingProcess->GetWrappedProcess()->PostStepDoIt(*track, *step);
  const auto fs_fg =
      dynamic_cast<G4ParticleChangeForGamma *>(processFinalStateForGamma);
  fParticleChange.Initialize(*track);
  fParticleChange.ProposeTrackStatus(fs_fg->GetTrackStatus());
  fParticleChange.ProposeEnergy(fs_fg->GetProposedKineticEnergy());
  fParticleChange.ProposeMomentumDirection(
      fs_fg->GetProposedMomentumDirection());
  // DDD(fs_fg->GetProposedKineticEnergy());

  // Copied from G4: "inform we take care of secondaries weight (otherwise these
  // secondaries are by default given the primary weight)."
  fParticleChange.SetSecondaryWeightByProcess(true);
  fParticleChange.SetParentWeightByProcess(true);

  // Loop to split Compton gammas
  fAAManager->StartAcceptLoop();
  std::vector<G4Track *> secondary_tracks;
  for (auto i = 0; i < fSplittingFactor; i++) {
    auto *processFinalState =
        callingProcess->GetWrappedProcess()->PostStepDoIt(*track, *step);
    const auto fs = dynamic_cast<G4ParticleChangeForGamma *>(processFinalState);
    auto momentum = fs->GetProposedMomentumDirection();

    // Angular Acceptance rejection
    if (!fAAManager->TestIfAccept(position, momentum)) {
      continue;
    }

    // Create a new track with another gamma
    const auto energy = fs->GetProposedKineticEnergy();
    auto gammaTrack = new G4Track(*track);
    // DDD(weight);
    gammaTrack->SetWeight(weight);
    gammaTrack->SetKineticEnergy(energy);
    gammaTrack->SetMomentumDirection(momentum);
    gammaTrack->SetPosition(position);

    // consider this gamma as a secondary
    secondary_tracks.push_back(gammaTrack);

    // FIXME secondaries electrons ? (ignored for now)
  }

  // Add secondaries
  fParticleChange.SetNumberOfSecondaries(secondary_tracks.size());
  for (const auto gammaTrack : secondary_tracks)
    fParticleChange.AddSecondary(gammaTrack);

  return &fParticleChange;
}
