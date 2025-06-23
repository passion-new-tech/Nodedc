
// chart.js pour les statistiques
document.addEventListener('DOMContentLoaded', function () {
new Chart(document.getElementById('chartPresences'), {
      type: 'line',
      data: {
        labels: ['Lun', 'Mar', 'Mer', 'Jeu', 'Ven'],
        datasets: [{
          label: 'Présences',
          data: [52, 50, 44, 20, 52],
          borderColor: '#ff7900',
          backgroundColor: 'rgba(255,121,0,0.2)',
          fill: true
        }]
      },
      options : {
        reponsive: true,
        plugins: {
            title: {
                display: true,
                text: 'Présences Hebdomadaires'
            },
            legend: {
                display: true,
                position: 'top'
            }
        },
    } 
    });

    new Chart(document.getElementById('chartProfils'), {
      type: 'doughnut',
      data: {
        labels: ['Dév', 'Design', 'Data'],
        datasets: [{
          label: 'Profils',
          data: [50, 30, 20],
          backgroundColor: ['#ff7900', '#27ae60', '#3498db']
        }]
      }
    });

    new Chart(document.getElementById('chartCandidatures'), {
      type: 'bar',
      data: {
        labels: ['Acceptées', 'En attente', 'Rejetées'],
        datasets: [{
          label: 'Candidatures',
          data: [20, 10, 5],
          backgroundColor: ['#27ae60', '#f1c40f', '#e74c3c']
        }]
      }
    });

    new Chart(document.getElementById('chartSync'), {
      type: 'pie',
      data: {
        labels: ['En ligne', 'Hors ligne'],
        datasets: [{
          label: 'Synchronisation',
          data: [85, 15],
          backgroundColor: ['#27ae60', '#7f8c8d']
        }]
      }
    });
});
