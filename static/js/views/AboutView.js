// Site override of Slotify's AboutView. The only behavioral difference is the
// config-driven author tab panel; the surrounding view and slot seams remain
// aligned with the theme component.
const { ref } = Vue;
const { useRoute } = VueRouter;
import StateFeedback from '../components/StateFeedback.js';
import BaseSurface from '../components/BaseSurface.js';
import SocialLinks from '../components/SocialLinks.js';
import PageHeader from '../components/PageHeader.js';
import FeaturedImage from '../components/FeaturedImage.js';
import ContentShell from '../components/ContentShell.js';
import { useAbout } from '../composables/useAbout.js';

export default {
  components: {
    StateFeedback,
    BaseSurface,
    SocialLinks,
    PageHeader,
    FeaturedImage,
    ContentShell
  },
  template: `
    <content-shell>
      <template #header>
        <page-header v-if="!error" icon="mdi-information-outline" :title="pageTitle"></page-header>
      </template>

      <state-feedback :error="error"></state-feedback>

      <slotify-slot name="aboutView/top" :ctx="{ pageData }"></slotify-slot>

      <base-surface v-if="!error" :hover-lift="false" class="pa-0 overflow-hidden">
        <featured-image :src="pageData.image" :alt="pageTitle" :max-height="400"></featured-image>

        <div class="pa-8">
          <slotify-slot name="aboutView/contentTop" :ctx="{ pageData }"></slotify-slot>

          <v-card-text class="text-body-1 pa-0 pb-6">
            <template v-if="pageData.authors && pageData.authors.length">
              <v-tabs
                v-if="pageData.showAuthorTabs"
                v-model="authorTab"
                color="primary"
                show-arrows
                class="mb-5"
                aria-label="Authors"
              >
                <v-tab
                  v-for="author in pageData.authors"
                  :key="author.id"
                  :value="author.id"
                  v-text="author.name"
                ></v-tab>
              </v-tabs>

              <v-window v-if="pageData.showAuthorTabs" v-model="authorTab">
                <v-window-item
                  v-for="author in pageData.authors"
                  :key="author.id"
                  :value="author.id"
                >
                  <div v-html="author.content" class="markdown-body"></div>
                </v-window-item>
              </v-window>

              <div
                v-else
                v-html="pageData.authors[0].content"
                class="markdown-body"
              ></div>
            </template>

            <div v-else v-html="pageData.content" class="markdown-body"></div>
          </v-card-text>

          <slotify-slot name="aboutView/contentBottom" :ctx="{ pageData }"></slotify-slot>
        </div>
      </base-surface>

      <slotify-slot name="aboutView/bottom" :ctx="{ pageData }"></slotify-slot>

      <template #aside-left>
        <slotify-slot name="aboutView/left" :ctx="{ pageData }"></slotify-slot>
      </template>
      <template #aside>
        <slotify-slot name="aboutView/right" :ctx="{ pageData }"></slotify-slot>
      </template>
    </content-shell>
  `,
  async setup() {
    const route = useRoute();
    const { pageData, pageTitle, error, siteConfig, fetchData } = useAbout();
    const authorTab = ref(null);

    await fetchData(route.path);

    if (pageData.value?.authors?.length) {
      authorTab.value = pageData.value.authors[0].id;
    }

    return { pageData, pageTitle, error, siteConfig, authorTab };
  }
};
