FROM mcr.microsoft.com/playwright:v1.50.0-noble

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm install

COPY . .

CMD ["sh", "-c", "sh /app/scripts/wait-for-web.sh && npx playwright test ${E2E_GREP:+--grep \"$E2E_GREP\"}"]
