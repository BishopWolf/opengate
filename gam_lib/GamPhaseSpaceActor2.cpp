/* --------------------------------------------------
   Copyright (C): OpenGATE Collaboration
   This software is distributed under the terms
   of the GNU Lesser General  Public Licence (LGPL)
   See LICENSE.md for further details
   -------------------------------------------------- */

#include <iostream>
#include "GamPhaseSpaceActor2.h"
#include "GamDictHelpers.h"
#include "GamHitsCollectionManager.h"

G4Mutex GamPhaseSpaceActor2Mutex = G4MUTEX_INITIALIZER;

GamPhaseSpaceActor2::GamPhaseSpaceActor2(py::dict &user_info)
    : GamVActor(user_info) {
    fActions.insert("StartSimulationAction");
    fActions.insert("EndSimulationAction");
    fActions.insert("BeginOfRunAction");
    fActions.insert("PreUserTrackingAction");
    fActions.insert("EndOfRunAction");
    fActions.insert("SteppingAction");
    fOutputFilename = DictStr(user_info, "output");
    fHitsCollectionName = DictStr(user_info, "name");
    fUserHitAttributeNames = DictVecStr(user_info, "attributes");
    fHits = nullptr;
}

GamPhaseSpaceActor2::~GamPhaseSpaceActor2() {
}

// Called when the simulation start
void GamPhaseSpaceActor2::StartSimulationAction() {
    fHits = GamHitsCollectionManager::GetInstance()->NewHitsCollection(fHitsCollectionName);
    fHits->SetFilename(fOutputFilename);
    fHits->InitializeHitAttributes(fUserHitAttributeNames);
    fHits->CreateRootTupleForMaster();
}

// Called when the simulation end
void GamPhaseSpaceActor2::EndSimulationAction() {
    fHits->Write(); // FIXME add an option to not write to disk
    fHits->Close();
}

// Called every time a Run starts
void GamPhaseSpaceActor2::BeginOfRunAction(const G4Run *) {
    fHits->CreateRootTupleForWorker();
}

// Called every time a Run ends
void GamPhaseSpaceActor2::EndOfRunAction(const G4Run *) {
    G4AutoLock mutex(&GamPhaseSpaceActor2Mutex);
    fHits->FillToRoot();
    // Only required when MT
    if (G4Threading::IsMultithreadedApplication())
        fHits->Write();
}

void GamPhaseSpaceActor2::BeginOfEventAction(const G4Event *) {
}

// Called every time a Track starts (even if not in the volume attached to this actor)
void GamPhaseSpaceActor2::PreUserTrackingAction(const G4Track *) {
    fThreadLocalData.Get().currentTrackAlreadyStored = false;
}

// Called every time a batch of step must be processed
void GamPhaseSpaceActor2::SteppingAction(G4Step *step, G4TouchableHistory *touchable) {
    // Only store if this is the first time 
    if (fThreadLocalData.Get().currentTrackAlreadyStored) return;
    fHits->ProcessHits(step, touchable);
    fThreadLocalData.Get().currentTrackAlreadyStored = true;
}
