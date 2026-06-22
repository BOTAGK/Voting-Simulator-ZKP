import {
  setupAdminDashboard,
  setupAdminLogin,
  setupAdminLogout,
  setupCreateElection,
} from "./admin.js";
import {
  setupVoterClearPackage,
  setupVoterPackageEntry,
} from "./voter-package.js";
import { setupVotePayload } from "./vote.js";

setupAdminLogin();
setupCreateElection();
setupAdminDashboard();
setupVotePayload();
setupAdminLogout();
setupVoterPackageEntry();
setupVoterClearPackage();
