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
import { renderLocalDateTimes } from "./shared.js";

renderLocalDateTimes();
setupAdminLogin();
setupCreateElection();
setupAdminDashboard();
setupVotePayload();
setupAdminLogout();
setupVoterPackageEntry();
setupVoterClearPackage();
