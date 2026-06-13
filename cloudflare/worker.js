import { Container, getContainer } from "@cloudflare/containers";

export class SkillSprintContainer extends Container {
  defaultPort = 8000;
  sleepAfter = "10m";
}

export default {
  async fetch(request, env) {
    const container = getContainer(env.SKILLSPRINT_CONTAINER);
    return container.fetch(request);
  },
};
