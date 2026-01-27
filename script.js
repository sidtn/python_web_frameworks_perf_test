import http from 'k6/http';


export const options = {
  vus: 20,
  duration: '60s',
};

export default function () {
  for (let id = 10000; id <= 12000; id++) {
    http.get(http.url`http://localhost:8000/orders/${id}`);
    http.get(http.url`http://localhost:8000/orders/${id}/lite`)
  }
}
